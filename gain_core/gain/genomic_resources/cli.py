"""Provides CLI for management of genomic resources repositories."""
import argparse
import copy
import fnmatch
import gzip
import json
import logging
import os
import pathlib
import sys
from collections.abc import Sequence
from typing import Any, cast
from urllib.parse import urlparse

import apsw
import yaml
from cerberus.schema import SchemaError
from jinja2 import Template

from gain import __version__  # type: ignore
from gain.genomic_resources.cached_repository import GenomicResourceCachedRepo
from gain.genomic_resources.fsspec_protocol import (
    FsspecReadWriteProtocol,
    FsspecRepositoryProtocol,
    build_fsspec_protocol,
)
from gain.genomic_resources.group_repository import GenomicResourceGroupRepo
from gain.genomic_resources.repository import (
    GR_CONF_FILE_NAME,
    GR_CONTENTS_FILE_NAME,
    GenomicResource,
    GenomicResourceRepo,
    ManifestEntry,
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
    parse_gr_id_version_token,
    version_tuple_to_string,
)
from gain.genomic_resources.repository_factory import (
    DEFAULT_DEFINITION,
    build_genomic_resource_repository,
    build_resource_implementation,
    get_default_grr_definition,
    get_default_grr_definition_path,
    load_definition_file,
)
from gain.genomic_resources.resource_implementation import (
    GenomicResourceImplementation,
    ResourceStatistics,
)
from gain.task_graph.cli_tools import TaskGraphCli
from gain.task_graph.graph import Task, TaskGraph, chain_tasks
from gain.utils import fs_utils
from gain.utils.fs_utils import (
    find_directory_with_a_file,
    find_subdirectories_with_a_file,
)
from gain.utils.helpers import convert_size
from gain.utils.verbosity_configuration import VerbosityConfiguration

logger = logging.getLogger("grr_manage")


def _add_repository_resource_parameters_group(
    parser: argparse.ArgumentParser, *, use_resource: bool = True,
) -> None:

    group = parser.add_argument_group(title="Repository/Resource")
    group.add_argument(
        "-R", "--repository", type=str,
        default=None,
        help="URL to the genomic resources repository. If not specified "
        "the tool assumes a local file system repository and starts looking "
        "for .CONTENTS.json file from the current working directory up to the "
        "root directory. If found the directory is assumed for root "
        "repository directory; otherwise error is reported.")
    group.add_argument(
        "--grr", "--definition", "-g", type=str,
        default=None,
        help="Path to an extra GRR definition file. This GRR will be loaded"
        "in a group alongside the local one.")

    group.add_argument(
        "--extra-args", type=str, default=None,
        help="comma separated list of `key=value` pairs arguments needed for "
        "connection to the specific repository protocol. "
        "Ex: if you want to connect to an S3 repository it is often "
        "neccessary to pass additional `endpoint-url` argument.",
    )
    if use_resource:
        group.add_argument(
            "-r", "--resource", type=str,
            help="Specifies the resource whose manifest we want to rebuild. "
            "If not specified the tool assumes local filesystem repository "
            "and starts looking for 'genomic_resource.yaml' file from "
            "current working directory up to the root directory. If found "
            "the directory is assumed for a resource directory; otherwise "
            "error is reported.")


def _add_dry_run_and_force_parameters_group(
        parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group(title="Force/Dry run")
    group.add_argument(
        "-n", "--dry-run", default=False, action="store_true",
        help="only checks if the manifest update is needed whithout "
        "actually updating it")
    group.add_argument(
        "-f", "--force", default=False,
        action="store_true",
        help="ignore resource state and rebuild manifest")


def _add_dvc_parameters_group(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group(title="DVC params")
    group.add_argument(
        "--with-dvc", default=True,
        action="store_true", dest="use_dvc",
        help="use '.dvc' files if present to get md5 sum of resource files "
        "(default)")
    group.add_argument(
        "-D", "--without-dvc", default=True,
        action="store_false", dest="use_dvc",
        help="calculate the md5 sum if necessary of resource files; "
        "do not use '.dvc' files to get md5 sum of resource files")


def _add_hist_parameters_group(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group(title="Statistics")
    group.add_argument(
        "--region-size", type=int, default=3_000_000_000,
        help="Region size to use for splitting statistics calculation into "
        "tasks")


def _configure_list_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("list", help="List a GR Repo")
    parser.add_argument(
        "--hr", default=False, action="store_true",
        help="Projects the size in human-readable format.")
    _add_repository_resource_parameters_group(parser, use_resource=False)
    VerbosityConfiguration.set_arguments(parser)


def _run_list_command(
        proto: ReadOnlyRepositoryProtocol | GenomicResourceRepo,
        args: argparse.Namespace) -> None:
    repos: list = [proto]
    if isinstance(proto, GenomicResourceGroupRepo):
        repos = proto.children
    for repo in repos:
        for res in repo.get_all_resources():
            res_size = sum(fs for _, fs in res.get_manifest().get_files())

            files_msg = f"{len(list(res.get_manifest().get_files())):2d}"
            if isinstance(repo, GenomicResourceCachedRepo):
                cached_files = repo.get_resource_cached_files(res.get_id())
                files_msg = f"{len(cached_files):2d}/{files_msg}"

            res_size_msg = res_size \
                if hasattr(args, "bytes") and args.bytes is True \
                else convert_size(res_size)
            repo_id = repo.repo_id if isinstance(repo, GenomicResourceRepo) \
                else repo.get_id()
            print(
                f"{res.get_type():20} {res.get_version_str():7s} "
                f"{files_msg} {res_size_msg:12} "
                f"{repo_id} "
                f"{res.get_id()}")


def _configure_repo_init_subparser(
        subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "repo-init", help="Initialize a directory to turn it into a GRR")

    _add_repository_resource_parameters_group(parser, use_resource=False)
    _add_dry_run_and_force_parameters_group(parser)
    VerbosityConfiguration.set_arguments(parser)


def _run_repo_init_command(**kwargs: str) -> None:
    repository: str | None = kwargs.get("repository")
    if repository is None:
        repo_url = find_directory_with_a_file(GR_CONTENTS_FILE_NAME)
        if repo_url is None:
            repo_url = find_directory_with_a_file(GR_CONTENTS_FILE_NAME[:-3])
    else:
        assert repository is not None
        repo_url = find_directory_with_a_file(
            GR_CONTENTS_FILE_NAME, repository)
        if repo_url is None:
            repo_url = find_directory_with_a_file(
                GR_CONTENTS_FILE_NAME[:-3], repository)

    if repo_url is not None:
        logger.error(
            "current working directory is part of a GRR at %s", repo_url)
        sys.exit(1)

    if repository is None:
        cwd = pathlib.Path().absolute()
    else:
        cwd = pathlib.Path(repository).absolute()

    proto = _create_proto(str(cwd))
    assert isinstance(proto, FsspecRepositoryProtocol)
    proto.build_content_file()


def _configure_repo_manifest_subparser(
        subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "repo-manifest", help="Create/update manifests for whole GRR")

    _add_repository_resource_parameters_group(parser, use_resource=False)
    _add_dry_run_and_force_parameters_group(parser)
    _add_dvc_parameters_group(parser)
    VerbosityConfiguration.set_arguments(parser)


def _configure_resource_manifest_subparser(
        subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "resource-manifest", help="Create/update manifests for a resource")

    _add_repository_resource_parameters_group(parser)
    _add_dry_run_and_force_parameters_group(parser)
    _add_dvc_parameters_group(parser)
    VerbosityConfiguration.set_arguments(parser)


def _configure_repo_stats_subparser(
        subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "repo-stats",
        help="Build the statistics for a resource")

    _add_repository_resource_parameters_group(parser, use_resource=False)
    _add_dry_run_and_force_parameters_group(parser)
    _add_dvc_parameters_group(parser)
    _add_hist_parameters_group(parser)
    VerbosityConfiguration.set_arguments(parser)

    TaskGraphCli.add_arguments(
        parser, use_commands=False, task_progress_mode=False,
    )


def _configure_resource_stats_subparser(
        subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "resource-stats",
        help="Build the statistics for a resource")

    _add_repository_resource_parameters_group(parser)
    _add_dry_run_and_force_parameters_group(parser)
    _add_dvc_parameters_group(parser)
    _add_hist_parameters_group(parser)
    VerbosityConfiguration.set_arguments(parser)

    TaskGraphCli.add_arguments(
        parser, use_commands=False, task_progress_mode=False,
    )


def _configure_repo_repair_subparser(
        subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "repo-repair",
        help="Update/rebuild manifest and histograms whole GRR")
    _add_repository_resource_parameters_group(parser, use_resource=False)
    _add_dry_run_and_force_parameters_group(parser)
    _add_dvc_parameters_group(parser)
    _add_hist_parameters_group(parser)
    VerbosityConfiguration.set_arguments(parser)

    TaskGraphCli.add_arguments(
        parser, use_commands=False, task_progress_mode=False,
    )


def _configure_resource_repair_subparser(
        subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "resource-repair",
        help="Update/rebuild manifest and histograms for a resource")
    _add_repository_resource_parameters_group(parser)
    _add_dry_run_and_force_parameters_group(parser)
    _add_dvc_parameters_group(parser)
    _add_hist_parameters_group(parser)
    VerbosityConfiguration.set_arguments(parser)

    TaskGraphCli.add_arguments(
        parser, use_commands=False, task_progress_mode=False,
    )


def _configure_repo_info_subparser(
        subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "repo-info", help="Build the index.html for the whole GRR",
    )
    _add_repository_resource_parameters_group(parser)
    _add_dry_run_and_force_parameters_group(parser)
    _add_dvc_parameters_group(parser)
    VerbosityConfiguration.set_arguments(parser)

    TaskGraphCli.add_arguments(
        parser, use_commands=False, task_progress_mode=False,
    )


def _configure_resource_info_subparser(
        subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "resource-info", help="Build the index.html for the specific resource",
    )
    _add_repository_resource_parameters_group(parser)
    _add_dry_run_and_force_parameters_group(parser)
    _add_dvc_parameters_group(parser)
    VerbosityConfiguration.set_arguments(parser)

    TaskGraphCli.add_arguments(
        parser, use_commands=False, task_progress_mode=False,
    )


def _configure_build_fts_db_subparser(
        subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "repo-build-fts", help="Build the FTS index for the whole GRR",
    )
    _add_repository_resource_parameters_group(parser)
    _add_dvc_parameters_group(parser)
    VerbosityConfiguration.set_arguments(parser)


def collect_dvc_entries(
        proto: ReadWriteRepositoryProtocol,
        res: GenomicResource) -> dict[str, ManifestEntry]:
    """Collect manifest entries defined by .dvc files."""
    result = {}
    manifest = proto.collect_resource_entries(res)
    for entry in manifest:
        if not entry.name.endswith(".dvc"):
            continue
        filename = entry.name[:-4]
        basename = os.path.basename(filename)

        if filename not in manifest:
            logger.info(
                "filling manifest of <%s> with entry for <%s> based on "
                "dvc data only",
                res.resource_id, filename)

        with proto.open_raw_file(res, entry.name, "rt") as infile:
            content = infile.read()
            dvc = yaml.safe_load(content)
            for data in dvc["outs"]:
                if data["path"] == basename:
                    result[filename] = \
                        ManifestEntry(filename, data["size"], data["md5"])

    return result


def _do_resource_stats_hash_and_manifest(
    proto: ReadWriteRepositoryProtocol,
    res: GenomicResource,
    dry_run: bool,  # noqa: FBT001
    force: bool,  # noqa: FBT001
    use_dvc: bool,  # noqa: FBT001
) -> None:
    _store_stats_hash(proto, res)
    _do_resource_manifest_command(
        proto, res,
        dry_run=dry_run,
        force=force,
        use_dvc=use_dvc)


def _do_resource_manifest_command(
    proto: ReadWriteRepositoryProtocol,
    res: GenomicResource,
    dry_run: bool,  # noqa: FBT001
    force: bool,  # noqa: FBT001
    use_dvc: bool,  # noqa: FBT001
) -> bool:
    prebuild_entries = {}
    if use_dvc:
        prebuild_entries = collect_dvc_entries(proto, res)

    manifest_update = proto.check_update_manifest(res, prebuild_entries)
    if not bool(manifest_update):
        logger.debug(
            "manifest of <%s> is up to date",
            res.get_genomic_resource_id_version())
    else:
        msg = (
            f"manifest of "
            f"<{res.get_genomic_resource_id_version()}> "
            f"should be updated; "
            f"entries to update in manifest "
            f"{sorted(manifest_update.entries_to_update)}"
        )
        if manifest_update.entries_to_delete:
            msg = (
                f"{msg}; "  # noqa: S608
                f"entries to delete from manifest "
                f"{sorted(manifest_update.entries_to_delete)}"
            )
        logger.warning(msg)

    if dry_run:
        return bool(manifest_update)

    if force:
        logger.info(
            "building manifest for resource <%s>...", res.resource_id)
        manifest = proto.build_manifest(
            res, prebuild_entries)
        proto.save_manifest(res, manifest)
        return False

    if bool(manifest_update):
        logger.info(
            "updating manifest for resource <%s>...", res.resource_id)
        manifest = proto.update_manifest(
            res, prebuild_entries)
        proto.save_manifest(res, manifest)
        return False
    return bool(manifest_update)


def _run_repo_manifest_command_internal(
        proto: ReadWriteRepositoryProtocol,
        resources: Sequence[GenomicResource],
        **kwargs: bool | int | str) -> dict[str, Any]:
    dry_run = cast(bool, kwargs.get("dry_run", False))
    force = cast(bool, kwargs.get("force", False))
    use_dvc = cast(bool, kwargs.get("use_dvc", True))

    updates_needed = {}
    for res in resources:
        updates_needed[res.resource_id] = _do_resource_manifest_command(
            proto, res,
            dry_run=dry_run,
            force=force,
            use_dvc=use_dvc,
        )

    if dry_run:
        return updates_needed

    assert isinstance(proto, FsspecReadWriteProtocol)
    proto.build_content_file()

    return updates_needed


def _run_build_fts_db_command(
    proto: FsspecReadWriteProtocol,
) -> None:
    content_filepath = os.path.join(
        proto.url, GR_CONTENTS_FILE_NAME)
    with proto.filesystem.open(
        content_filepath, mode="r", compression="gzip",
    ) as contents_file:
        contents = json.loads(contents_file.read())
        _create_contents_db(proto, contents)


def _create_contents_db(
    proto: FsspecReadWriteProtocol,
    contents: list[dict[str, Any]],
) -> None:

    sqlite_filepath = proto.filesystem.expand_path(".CONTENTS.sqlite3")[0]
    gzip_sqlite_filepath = f"{sqlite_filepath}.gz"
    if os.path.exists(sqlite_filepath):
        os.remove(sqlite_filepath)
    if os.path.exists(gzip_sqlite_filepath):
        os.remove(gzip_sqlite_filepath)
    with apsw.Connection(sqlite_filepath) as conn:

        labels = set()

        for res_info in contents:
            res_labels = res_info["config"].get("meta", {}).get("labels", {})
            if res_labels is None:
                res_labels = {}
            labels.update(res_labels.keys())

        label_list = list(labels)  # switch to list for ordered access
        if len(label_list) > 0:
            # Empty label is added for more convenient support of queries
            # without labels. ", ".join(labels) would start with a "," when
            # labes are present and without when they are not.
            label_list.insert(0, "")

        conn.execute(
            "CREATE TABLE contents_metadata (key TEXT PRIMARY KEY, value TEXT)",
        )
        conn.execute(
            "INSERT INTO contents_metadata (key, value) VALUES (?, ?)",
            ("contents_md5", proto.md5_contents()),
        )

        conn.execute(
            "CREATE VIRTUAL TABLE contents "
            "USING fts5(full_id, id, type, description, summary"
            f"{', '.join(label_list)})",
        )

        for res_info in contents:
            res_full_id = res_info["full_id"]
            res_id = res_info["id"]
            res_type = res_info["config"]["type"]
            res_description = res_info["config"].get("meta", {}).get(
                "description", "")
            res_summary = res_info["config"].get("meta", {}).get(
                "summary", "")

            res_labels = res_info["config"].get(
                "meta", {}).get("labels", {})

            if res_labels is None:
                res_labels = {}

            row = [
                res_full_id,
                res_id,
                res_type,
                res_description,
                res_summary,
                *[res_labels.get(label, "") for label in labels],
            ]

            conn.execute(
                "INSERT INTO contents "  # noqa: S608
                "(full_id, id, type, description, summary"
                f"{', '.join(label_list)}) "
                f"VALUES ({', '.join(['?' for _ in range(len(row))])})",
                (
                    *row,
                ),
            )

    raw_data = pathlib.Path(sqlite_filepath).read_bytes()
    with gzip.open(gzip_sqlite_filepath, mode="wb") as gzip_out:
        gzip_out.write(raw_data)
    os.remove(sqlite_filepath)


def _run_repo_manifest_command(
    proto: ReadWriteRepositoryProtocol,
    resources: Sequence[GenomicResource],
    **kwargs: bool | int | str,
) -> int:
    dry_run = cast(bool, kwargs.get("dry_run", False))
    force = cast(bool, kwargs.get("force", False))
    if dry_run and force:
        logger.warning("please choose one of 'dry_run' and 'force' options")
        return 1
    updates_needed = _run_repo_manifest_command_internal(
        proto, resources, **kwargs)
    if dry_run:
        return len(updates_needed)
    return 0


def _find_resources(
    proto: ReadOnlyRepositoryProtocol,
    repo_url: str,
    **kwargs: str | bool | int,
) -> Sequence[GenomicResource]:
    resource_pattern = cast(str, kwargs.get("resource"))

    if resource_pattern is not None:
        return [
            res for res in proto.get_all_resources()
            if fnmatch.fnmatch(res.resource_id, resource_pattern)
        ]

    if urlparse(repo_url).scheme not in {"file", ""}:
        logger.error(
            "resource not specified but the repository URL %s "
            "is not local filesystem repository", repo_url)
        return []

    cwd = os.getcwd()
    resource_dir = find_directory_with_a_file(GR_CONF_FILE_NAME, cwd)
    if resource_dir is not None:

        rid_ver = os.path.relpath(resource_dir, repo_url)
        resource_id, version = parse_gr_id_version_token(rid_ver)

        res = proto.get_resource(
            resource_id,
            version_constraint=f"={version_tuple_to_string(version)}")
        return [res]

    result = []
    for res_dir in find_subdirectories_with_a_file(GR_CONF_FILE_NAME, cwd):
        rid_ver = os.path.relpath(res_dir, repo_url)
        resource_id, version = parse_gr_id_version_token(rid_ver)

        res = proto.get_resource(
            resource_id,
            version_constraint=f"={version_tuple_to_string(version)}")
        result.append(res)
    if result:
        return result

    logger.error("Can't find resource starting from %s", cwd)
    return []


def _read_stats_hash(
        proto: ReadWriteRepositoryProtocol,
        implementation: GenomicResourceImplementation) -> bytes | None:
    res = implementation.resource
    stats_dir = ResourceStatistics.get_statistics_folder()
    if not proto.file_exists(res, f"{stats_dir}/stats_hash"):
        return None
    with proto.open_raw_file(
        res, f"{stats_dir}/stats_hash", mode="rb",
    ) as infile:
        return cast(bytes, infile.read())


def _store_stats_hash(
    proto: ReadWriteRepositoryProtocol,
    resource: GenomicResource,
    *args: Any,  # noqa: ARG001
) -> bool:

    impl = build_resource_implementation(resource)
    stats_dir = ResourceStatistics.get_statistics_folder()
    if stats_dir is None:
        logger.warning(
            "Couldn't store stats hash for %s; unable to get stats dir",
            resource.resource_id)
        return False
    with proto.open_raw_file(
        resource, f"{stats_dir}/stats_hash", mode="wb",
    ) as outfile:
        stats_hash = impl.calc_statistics_hash()
        outfile.write(stats_hash)
    return True


def _collect_impl_stats_tasks(  # pylint: disable=too-many-arguments
    graph: TaskGraph,
    proto: ReadWriteRepositoryProtocol,
    impl: GenomicResourceImplementation,
    grr: GenomicResourceRepo,
    *,
    dry_run: bool,
    force: bool,
    use_dvc: bool,
    region_size: int,
) -> None:

    tasks = impl.create_statistics_build_tasks(
        region_size=region_size, grr=grr)

    last_task: list[Task] = [tasks[-1].task] if len(tasks) > 0 else []
    manifest_task = graph.make_task(
        f"{impl.resource.get_full_id()}_stats_hash_and_manifest_rebuild",
        _do_resource_stats_hash_and_manifest,
        args=[proto, impl.resource, dry_run, force, use_dvc],
        deps=last_task,
    )
    if len(tasks) == 1:
        merged_task = chain_tasks(tasks[0], manifest_task)
        graph.add_task(merged_task)
    else:
        graph.add_tasks(tasks)
        graph.add_task(manifest_task)


def _stats_need_rebuild(
        proto: ReadWriteRepositoryProtocol,
        impl: GenomicResourceImplementation) -> bool:
    """Check if an implementation's stats need rebuilding."""
    current_hash = impl.calc_statistics_hash()
    stored_hash = _read_stats_hash(proto, impl)

    if stored_hash is None:
        logger.info(
            "No hash stored for <%s>; needs update",
            impl.resource.get_full_id(),
        )
        return True

    if stored_hash != current_hash:
        logger.info(
            "Stored hash for <%s> is outdated; needs update",
            impl.resource.get_full_id(),
        )
        return True

    logger.debug(
        "<%s> statistics hash is up to date", impl.resource.get_full_id(),
    )
    return False


def _run_repo_stats_command(
        repo: GenomicResourceRepo,
        proto: ReadWriteRepositoryProtocol,
        resources: Sequence[GenomicResource],
        **kwargs: bool | int | str) -> int:
    dry_run = cast(bool, kwargs.get("dry_run", False))
    force = cast(bool, kwargs.get("force", False))
    use_dvc = cast(bool, kwargs.get("use_dvc", True))
    region_size = cast(int, kwargs.get("region_size", 3_000_000))

    if dry_run and force:
        logger.warning("please choose one of 'dry_run' and 'force' options")
        return 0

    updates_needed = _run_repo_manifest_command_internal(
        proto, resources, **kwargs)

    graph = TaskGraph()

    status = 0
    for res in resources:
        if updates_needed[res.resource_id]:
            status += 1
            logger.info(
                "Manifest of <%s> needs update, cannot check statistics",
                res.resource_id,
            )
            continue
        impl = build_resource_implementation(res)
        needs_rebuild = _stats_need_rebuild(proto, impl)
        if (force or needs_rebuild) and not dry_run:
            _collect_impl_stats_tasks(
                graph, proto, impl, repo,
                dry_run=dry_run,
                force=force,
                use_dvc=use_dvc,
                region_size=region_size)
        elif dry_run and needs_rebuild:
            logger.info("Statistics of <%s> needs update", res.resource_id)
            status += 1

    if dry_run:
        return status

    if len(graph.tasks) > 0:
        modified_kwargs = copy.copy(kwargs)
        modified_kwargs["command"] = "run"
        if modified_kwargs.get("task_log_dir") is None:
            repo_url = proto.get_url()
            modified_kwargs["task_log_dir"] = \
                fs_utils.join(repo_url, ".task-log")

        TaskGraphCli.process_graph(
            graph, task_progress_mode=False, **modified_kwargs)

    return 0


def _run_repo_repair_command(
        repo: GenomicResourceRepo,
        proto: ReadWriteRepositoryProtocol,
        resources: Sequence[GenomicResource],
        **kwargs: str | bool | int) -> int:
    return _run_repo_info_command(repo, proto, resources, **kwargs)


def _run_repo_info_command(
        repo: GenomicResourceRepo,
        proto: ReadWriteRepositoryProtocol,
        resources: Sequence[GenomicResource],
        **kwargs: str | bool | int) -> int:
    status = _run_repo_stats_command(repo, proto, resources, **kwargs)

    dry_run = cast(bool, kwargs.get("dry_run", False))
    if dry_run:
        return status

    proto.build_index_info(repository_template)  # type: ignore
    for res in resources:
        try:
            _do_resource_info_command(repo, proto, res)
        except ValueError:
            logger.exception(
                "Failed to generate repo index for %s",
                res.resource_id,
            )
        except SchemaError:
            logger.exception(
                "Resource %s has an invalid configuration",
                res.resource_id,
            )
        except BaseException:  # pylint: disable=broad-except
            logger.exception(
                "Failed to load %s",
                res.resource_id,
            )
    return 0


def _do_resource_info_command(
        repo: GenomicResourceRepo,
        proto: ReadWriteRepositoryProtocol,
        res: GenomicResource) -> None:
    implementation = build_resource_implementation(res)

    with proto.open_raw_file(res, "index.html", mode="wt") as outfile:
        content = implementation.get_info(repo=repo)
        outfile.write(content)

    with proto.open_raw_file(
        res,
        "statistics/index.html",
        mode="wt",
    ) as outfile:
        content = implementation.get_statistics_info(repo=repo)
        outfile.write(content)


def cli_manage(cli_args: list[str] | None = None) -> None:
    """Provide CLI for repository management."""
    # flake8: noqa: C901
    # pylint: disable=too-many-branches,too-many-statements
    if cli_args is None:
        cli_args = sys.argv[1:]
    desc = "Genomic Resource Repository Management Tool"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "--version", action="store_true", default=False,
        help="Prints GPF version and exists.")
    VerbosityConfiguration.set_arguments(parser)

    commands_parser: argparse._SubParsersAction = parser.add_subparsers(
        dest="command", help="Command to execute")

    _configure_list_subparser(commands_parser)
    _configure_repo_init_subparser(commands_parser)
    _configure_repo_manifest_subparser(commands_parser)
    _configure_resource_manifest_subparser(commands_parser)
    _configure_repo_stats_subparser(commands_parser)
    _configure_resource_stats_subparser(commands_parser)
    _configure_repo_info_subparser(commands_parser)
    _configure_resource_info_subparser(commands_parser)
    _configure_repo_repair_subparser(commands_parser)
    _configure_resource_repair_subparser(commands_parser)
    _configure_build_fts_db_subparser(commands_parser)

    args = parser.parse_args(cli_args)
    VerbosityConfiguration.set(args)

    if args.version:
        print(f"GPF version: {__version__}")
        sys.exit(0)

    command = args.command
    if command is None:
        logger.error("missing grr_manage subcommand")
        parser.print_help()
        sys.exit(1)

    if command == "repo-init":
        _run_repo_init_command(**vars(args))
        return

    repo_url = _get_repo_url(args)
    repo = _create_grr_repo(args, repo_url)
    proto = _create_proto(repo_url, args.extra_args)
    if command == "list":
        _run_list_command(proto, args)
        return

    if not isinstance(proto, ReadWriteRepositoryProtocol):
        raise TypeError(
            f"resource management works with RW protocols; "
            f"{proto.proto_id} ({proto.scheme}) is read only")

    resources: Sequence[GenomicResource]

    if command in {"repo-manifest", "repo-stats", "repo-info", "repo-repair"}:
        status = 0
        resources = list(proto.get_all_resources())
        if len(resources) == 0:
            logger.info("repository <%s> has no resources", repo_url)
            sys.exit(0)

        try:
            if command == "repo-manifest":
                status = _run_repo_manifest_command(
                    proto, resources, **vars(args))
            elif command == "repo-stats":
                status = _run_repo_stats_command(
                    repo, proto, resources, **vars(args))
            elif command == "repo-info":
                status = _run_repo_info_command(
                    repo, proto, resources, **vars(args))
            elif command == "repo-repair":
                status = _run_repo_repair_command(
                    repo, proto, resources, **vars(args))
            else:
                logger.error(
                    "Unknown command %s.", command)
                sys.exit(1)
            if status == 0:
                logger.info("GRR <%s> is consistent", repo_url)
                return
        except ValueError as ex:
            logger.error(  # noqa: TRY400
                "Misconfigured repository %s; %s", repo_url, ex)
            status = 1

        logger.warning("inconsistent GRR <%s> state", repo_url)
        sys.exit(status)
    elif command in {
            "resource-manifest", "resource-stats",
            "resource-info", "resource-repair"}:
        status = 0
        resources = _find_resources(proto, repo_url, **vars(args))
        if not resources:
            logger.error("resource not found...")
            sys.exit(1)
        assert resources
        try:
            if command == "resource-manifest":
                status = _run_repo_manifest_command(
                    proto, resources, **vars(args))
            elif command == "resource-stats":
                status = _run_repo_stats_command(
                    repo, proto, resources, **vars(args))
            elif command == "resource-info":
                status = _run_repo_info_command(
                    repo, proto, resources, **vars(args))
            elif command == "resource-repair":
                status = _run_repo_repair_command(
                    repo, proto, resources, **vars(args))
            else:
                logger.error(
                    "Unknown command %s.", command)
                sys.exit(1)
            if status == 0:
                logger.info("GRR <%s> is consistent", repo_url)
                return
        except ValueError:
            logger.exception("unexpected exception")
            status = 1
        logger.warning("inconsistent GRR <%s> state", repo_url)
        sys.exit(status)
    elif command == "repo-build-fts":
        assert isinstance(proto, FsspecReadWriteProtocol)
        _run_build_fts_db_command(proto)
        return
    else:
        logger.error(
            "Unknown command %s. The known commands are index, "
            "list and histogram", command)
        sys.exit(1)


def _create_grr_repo(
    args: argparse.Namespace,
    repo_url: str,
) -> GenomicResourceRepo:
    extra_definition_path = args.grr
    if extra_definition_path:
        if not os.path.exists(extra_definition_path):
            raise FileNotFoundError(
                f"Definition {extra_definition_path} not found!",
            )
        extra_definition = load_definition_file(extra_definition_path)
    else:
        extra_definition = get_default_grr_definition()
    grr_definition = {
        "id": "cli_grr",
        "type": "group",
        "children": [
            {
                "id": "local",
                "type": "dir",
                "directory": repo_url,
            },
            extra_definition,
        ],
    }

    return build_genomic_resource_repository(definition=grr_definition)


def _get_repo_url(args: argparse.Namespace) -> str:
    repo_url = args.repository
    if repo_url is None:
        repo_url = find_directory_with_a_file(GR_CONTENTS_FILE_NAME)
        if repo_url is None:
            repo_url = find_directory_with_a_file(GR_CONTENTS_FILE_NAME[:-3])
        if repo_url is None:
            logger.error(
                "Can't find repository starting from: %s", os.getcwd())
            sys.exit(1)
        repo_url = str(repo_url)
        print(f"working with repository: {repo_url}")

    return cast(str, repo_url)


def _create_proto(
    repo_url: str, extra_args: str = "",
) -> ReadWriteRepositoryProtocol:
    url = urlparse(repo_url)

    if url.scheme in {"file", ""} and not os.path.isabs(repo_url):
        repo_url = os.path.abspath(repo_url)

    kwargs: dict[str, str] = {}
    if extra_args:
        parsed = [tuple(a.split("=")) for a in extra_args.split(",")]
        kwargs = {p[0]: p[1] for p in parsed}

    proto = build_fsspec_protocol(
        proto_id="manage", root_url=repo_url, **kwargs)
    if not isinstance(proto, ReadWriteRepositoryProtocol):
        raise TypeError(f"repository protocol is not writable: {repo_url}")
    return proto


def cli_browse(cli_args: list[str] | None = None) -> None:
    """Provide CLI for repository browsing."""
    desc = "Genomic Resource Repository Browse Tool"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "--version", action="store_true", default=False,
        help="Prints GPF version and exists.")
    VerbosityConfiguration.set_arguments(parser)

    group = parser.add_argument_group(title="Repository/Resource")
    group.add_argument(
        "-g", "--grr", type=str,
        default=None,
        help="path to GRR definition file.")

    parser.add_argument(
        "--bytes",
        default=False,
        action="store_true",
        help="Print the resource size in bytes",
    )

    if cli_args is None:
        cli_args = sys.argv[1:]
    args = parser.parse_args(cli_args)
    VerbosityConfiguration.set(args)

    if args.version:
        print(f"GPF version: {__version__}")
        sys.exit(0)

    definition_path = args.grr if args.grr is not None \
        else get_default_grr_definition_path()
    definition = load_definition_file(definition_path) \
        if definition_path is not None \
        else DEFAULT_DEFINITION

    if definition_path is not None:
        print("Working with GRR definition:", definition_path)
    else:
        print("No GRR definition found, using the DEFAULT_DEFINITION")
    print(yaml.safe_dump(definition, sort_keys=False))

    repo = build_genomic_resource_repository(definition=definition)
    _run_list_command(repo, args)


def get_scripts_for_template() -> str:
    scripts_file = pathlib.Path(__file__).parent / "repo_info_scripts.html"
    return scripts_file.read_text()


PAGE_HEAD = """
    <head>
     <link
      rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
    <style>
      * {
        font-family: sans-serif
      }

      th {
        background: #ecf1f6;
      }

      td, th {
        border: 1px solid #cfd8df;
        padding: 5px;
        max-width: 100px;
      }

      tr {
        height: 38px;
      }

      table, td, th {
        border-collapse: collapse;
      }

      a {
        text-decoration: none;
        color: #24699E;
      }

      a:hover {
        color: #4C93C9;
      }

      #search-container {
        margin-top: 10px;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 15px;
        position: sticky;
        top: 0;
        background-color: white;
        height: 70px;
      }

      #type-label {
        color: #5b778c;
      }

      #type-filter {
        border: 1px solid #85a2b9;
        height: 40px;
        border-radius: 5px;
        font-size: 18px;
        padding-left: 10px;
        background: white;
      }

      #type-filter:hover {
        cursor: pointer;
      }

      #search-field {
        width: 40%;
        border: 1px solid #85a2b9;
        height: 40px;
        border-radius: 5px;
        font-size: 18px;
        padding: 0 10px;
      }

      input::placeholder {
        color: #ababab;
      }

      #type-filter:focus-visible,
      #search-field:focus-visible,
      #type-filter:focus,
      #search-field:focus {
        outline-color: #85a2b9;
      }

      .nowrap {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .search-info {
        text-align: center;
        font-size: 0.9em;
        color: #ababab;
        font-style: italic;
        word-break: break-word;
        margin: 0 10%;
      }

      .loading,
      .searching {
        text-align: center;
        font-size: larger;
      }

      .pageButton {
        border: none;
        background: none;
        color: blue;
        cursor: pointer;
        padding: 3px;
        margin: 0px 3px;
      }

      .pageButton.active {
        color: black;
        cursor: default;
      }

      .pageButton.hide {
        display: none;
      }

      #status,
      #status-error {
        margin-left: 10%;
        margin-top: 15px;
        color: #5b778c;
      }

      #status-error {
        color: #d74b59;
        text-align: center;
      }

      #resource-table {
        margin: 10px 10%;
        width: 80%;
        border: 1px solid black;
      }

      .version-cell {
        width: 5%;
      }

      .size-cell,
      .type-cell {
        width: 10%;
      }

      .id-wrapper {
        display: flex;
        gap: 10px;
        align-items: center;
      }

      .id-cell {
        min-width: 50%;
        width: 50%;
      }

      .copy-icon {
        font-size: 20px;
        color: #B9D3E7;
      }

      .copy-icon:hover {
        cursor: pointer;
        color: #85A2B9;
      }

      #section-about {
        margin: 60px 10%;
        color: #333;
        line-height: 1.6;
      }

      #section-about h1 {
        font-size: 1.5em;
      }

      #page-header {
        position: relative;
        text-align: center;
        margin: 20px 10% 0;
      }

      #page-header h1 {
        margin: 0;
        display: inline-block;
      }

      #page-header h1 a {
        color: inherit;
        text-decoration: none;
      }

      #page-header h1 a:hover {
        color: inherit;
        cursor: pointer;
      }

      #nav-about {
        display: block;
        text-align: right;
        font-weight: bold;
        color: #7996ac;
        text-decoration: none;
        font-size: 20px;
      }

      #nav-about:hover {
        color: #8dabc1;
      }
    </style>
 </head>"""  # noqa: E501

INDEX_BODY = """
 <body>
     {% if has_about %}
     <div id="page-header">
       <a id="nav-about" href="about.html">About</a>
     </div>
     {% endif %}
     <div id="section-resources">
        <p class="loading">Loading search</p>
        <div id="search-container" style="display: none;">
          <span id="type-label">Resource type</span>
          <div id="type-cell">
            <select id="type-filter">
                <option value="all">All</option>
            </select>
          </div>
          <input type="text" id="search-field" placeholder="Search">
        </div>
        <div class="search-info">
          <div>
            use AND to perform 'and',
            use OR to perform 'or',
            use spaces to separate strings,
            surround strings in "" to use spaces inside the string
          </div>
          The search uses
          <a
            href="https://sqlite.org/fts5.html#full_text_query_syntax"
            target="_blank">
            SQLite's FTS syntax.</a>
        </div>
        <p id="status-error"></p>
        <div id="status"></div>
        <table id="resource-table" class="contents">
          <thead>
            <tr>
              <th class="nowrap type-cell">Type</th>
              <th class="nowrap id-cell">ID</th>
              <th class="nowrap version-cell">Version</th>
              <th
                class="nowrap size-cell"
                title="Total size (bytes)"
              >Total size (bytes)</th>
              <th class="nowrap">Summary</th>
            </tr>
          </thead>
          <tbody>
            {%- for key, value in data.items() recursive%}
            <tr id="{{value['res_full_id']}}">
              <td
                class="nowrap type-cell"
                title="{{value['type']}}"
              >{{value['type']}}</td>
              <td class="id-cell" title="{{key}}">
                <div class="id-wrapper">
                  <a class="nowrap" href='{{key}}/index.html'>{{key}}</a>
                  <span class="material-symbols-outlined copy-icon {{key}}">content_copy</span>
                </div>
              </td>
              <td class="nowrap version-cell">{{value['res_version']}}</td>
              <td class="nowrap size-cell">{{value['res_size']}}</td>
              <td
                class="nowrap"
                title="{{value['res_summary']}}"
              >{{value['res_summary']}}</td>
              </tr>
            {%- endfor %}
          </tbody>
        </table>
        <p class="searching" style="display: none;">Searching</p>
     </div>
     <div class="pagination"></div>
     </div>
     {% if has_about %}
     <div id="section-about" style="display: none;" class="content">
       {{about_contents}}
     </div>
     {% endif %}
 </body>
"""  # noqa: E501


ABOUT_BODY = """
    <body>
        <div id="section-about">
        {{about_contents}}
        </div>
    </body>
"""

repository_template = Template(
    "<html>\n" +
    PAGE_HEAD + get_scripts_for_template() + INDEX_BODY +
    "</html>",
)

about_template = Template(
    "<html>\n" + PAGE_HEAD + ABOUT_BODY + "</html>",
)
