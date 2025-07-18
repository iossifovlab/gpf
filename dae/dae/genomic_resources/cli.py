"""Provides CLI for management of genomic resources repositories."""
import argparse
import copy
import logging
import os
import pathlib
import sys
from typing import Any, cast
from urllib.parse import urlparse

import yaml
from cerberus.schema import SchemaError
from jinja2 import Template

from dae import __version__  # type: ignore
from dae.genomic_resources.cached_repository import GenomicResourceCachedRepo
from dae.genomic_resources.fsspec_protocol import build_fsspec_protocol
from dae.genomic_resources.group_repository import GenomicResourceGroupRepo
from dae.genomic_resources.repository import (
    GR_CONF_FILE_NAME,
    GR_CONTENTS_FILE_NAME,
    GenomicResource,
    GenomicResourceRepo,
    ManifestEntry,
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
    parse_resource_id_version,
    version_tuple_to_string,
)
from dae.genomic_resources.repository_factory import (
    DEFAULT_DEFINITION,
    build_genomic_resource_repository,
    build_resource_implementation,
    get_default_grr_definition,
    get_default_grr_definition_path,
    load_definition_file,
)
from dae.genomic_resources.resource_implementation import (
    GenomicResourceImplementation,
    ResourceStatistics,
)
from dae.task_graph.cli_tools import TaskGraphCli
from dae.task_graph.graph import TaskGraph
from dae.utils import fs_utils
from dae.utils.fs_utils import find_directory_with_a_file
from dae.utils.helpers import convert_size
from dae.utils.verbosity_configuration import VerbosityConfiguration

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
        "--region-size", type=int, default=300_000_000,
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
    else:
        assert repository is not None
        repo_url = find_directory_with_a_file(
            GR_CONTENTS_FILE_NAME, repository)

    if repo_url is not None:
        logger.error(
            "current working directory is part of a GRR at %s", repo_url)
        sys.exit(1)

    if repository is None:
        cwd = pathlib.Path().absolute()
    else:
        cwd = pathlib.Path(repository).absolute()

    proto = _create_proto(str(cwd))
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
        **kwargs: bool | int | str) -> dict[str, Any]:
    dry_run = cast(bool, kwargs.get("dry_run", False))
    force = cast(bool, kwargs.get("force", False))
    use_dvc = cast(bool, kwargs.get("use_dvc", True))

    updates_needed = {}
    for res in proto.get_all_resources():
        updates_needed[res.resource_id] = _do_resource_manifest_command(
            proto, res,
            dry_run=dry_run,
            force=force,
            use_dvc=use_dvc,
        )

    if not dry_run:
        proto.build_content_file()

    return updates_needed


def _run_repo_manifest_command(
    proto: ReadWriteRepositoryProtocol,
    **kwargs: bool | int | str,
) -> int:
    dry_run = cast(bool, kwargs.get("dry_run", False))
    force = cast(bool, kwargs.get("force", False))
    if dry_run and force:
        logger.warning("please choose one of 'dry_run' and 'force' options")
        return 1
    updates_needed = _run_repo_manifest_command_internal(proto, **kwargs)
    if dry_run:
        return len(updates_needed)
    return 0


def _find_resource(
        proto: ReadOnlyRepositoryProtocol,
        repo_url: str,
        **kwargs: str | bool | int) -> GenomicResource | None:
    resource_id = cast(str, kwargs.get("resource"))
    if resource_id is not None:
        res = proto.get_resource(resource_id)
    else:
        if urlparse(repo_url).scheme not in {"file", ""}:
            logger.error(
                "resource not specified but the repository URL %s "
                "is not local filesystem repository", repo_url)
            return None

        cwd = os.getcwd()
        resource_dir = find_directory_with_a_file(GR_CONF_FILE_NAME, cwd)
        if resource_dir is None:
            logger.error("Can't find resource starting from %s", cwd)
            return None

        rid_ver = os.path.relpath(resource_dir, repo_url)
        resource_id, version = parse_resource_id_version(rid_ver)

        res = proto.get_resource(
            resource_id,
            version_constraint=f"={version_tuple_to_string(version)}")
    return res


def _run_resource_manifest_command_internal(
        proto: ReadWriteRepositoryProtocol,
        repo_url: str, **kwargs: bool | int | str) -> bool:
    dry_run = cast(bool, kwargs.get("dry_run", False))
    force = cast(bool, kwargs.get("force", False))
    use_dvc = cast(bool, kwargs.get("use_dvc", True))

    res = _find_resource(proto, repo_url, **kwargs)
    if res is None:
        logger.error("resource not found...")
        return False
    return _do_resource_manifest_command(
        proto, res,
        dry_run=dry_run,
        force=force,
        use_dvc=use_dvc)


def _run_resource_manifest_command(
    proto: ReadWriteRepositoryProtocol,
    repo_url: str, **kwargs: bool | int | str,
) -> int:
    dry_run = cast(bool, kwargs.get("dry_run", False))
    force = cast(bool, kwargs.get("force", False))

    if dry_run and force:
        logger.warning("please choose one of 'dry_run' and 'force' options")
        return 1

    needs_update = _run_resource_manifest_command_internal(
        proto, repo_url, **kwargs)
    if dry_run:
        return int(needs_update)
    return 0


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
        resource: GenomicResource) -> bool:

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

    tasks = impl.add_statistics_build_tasks(
        graph, region_size=region_size, grr=grr)

    # This is the hack to update stats_hash without recreaing the histograms.
    graph.create_task(
        f"{impl.resource.get_full_id()}_store_stats_hash",
        _store_stats_hash,
        args=[proto, impl.resource],
        deps=tasks,
    )

    graph.create_task(
        f"{impl.resource.get_full_id()}_manifest_rebuild",
        _do_resource_manifest_command,
        args=[proto, impl.resource, dry_run, force, use_dvc],
        deps=tasks,
    )


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
        **kwargs: bool | int | str) -> int:
    dry_run = cast(bool, kwargs.get("dry_run", False))
    force = cast(bool, kwargs.get("force", False))
    use_dvc = cast(bool, kwargs.get("use_dvc", True))
    region_size = cast(int, kwargs.get("region_size", 3_000_000))

    if dry_run and force:
        logger.warning("please choose one of 'dry_run' and 'force' options")
        return 0

    updates_needed = _run_repo_manifest_command_internal(proto, **kwargs)

    graph = TaskGraph()

    status = 0
    for res in proto.get_all_resources():
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

    proto.build_content_file()
    return 0


def _run_resource_stats_command(
        repo: GenomicResourceRepo,
        proto: ReadWriteRepositoryProtocol,
        repo_url: str,
        **kwargs: bool | int | str) -> int:
    needs_update = _run_resource_manifest_command_internal(
        proto, repo_url, **kwargs)
    dry_run = cast(bool, kwargs.get("dry_run", False))
    force = cast(bool, kwargs.get("force", False))
    use_dvc = cast(bool, kwargs.get("use_dvc", True))
    region_size = cast(int, kwargs.get("region_size", 3_000_000))

    res = _find_resource(proto, repo_url, **kwargs)
    if res is None:
        raise ValueError("can't find resource")

    if dry_run and force:
        logger.warning("please choose one of 'dry_run' and 'force' options")
        return 1

    if res is None:
        logger.error("unable to find resource...")
        return 1

    if dry_run and needs_update:
        logger.info(
            "Manifest of <%s> needs update, cannot check statistics",
            res.resource_id,
        )
        return 1

    impl = build_resource_implementation(res)

    needs_rebuild = _stats_need_rebuild(proto, impl)

    if dry_run and needs_rebuild:
        logger.info("Statistics of <%s> needs update", res.resource_id)
        return 1

    if (force or needs_rebuild) and not dry_run:
        graph = TaskGraph()
        _collect_impl_stats_tasks(
            graph, proto, impl, repo,
            dry_run=dry_run,
            force=force, use_dvc=use_dvc,
            region_size=region_size)
        if len(graph.tasks) == 0:
            return 0

        modified_kwargs = copy.copy(kwargs)
        modified_kwargs["command"] = "run"
        if modified_kwargs.get("task_log_dir") is None:
            repo_url = proto.get_url()
            modified_kwargs["task_log_dir"] = \
                fs_utils.join(repo_url, ".task-log")

        TaskGraphCli.process_graph(
            graph, task_progress_mode=False, **modified_kwargs,
        )
    return 0


def _run_repo_repair_command(
        repo: GenomicResourceRepo,
        proto: ReadWriteRepositoryProtocol,
        **kwargs: str | bool | int) -> int:
    return _run_repo_info_command(repo, proto, **kwargs)


def _run_resource_repair_command(
        repo: GenomicResourceRepo,
        proto: ReadWriteRepositoryProtocol,
        repo_url: str,
        **kwargs: str | bool | int) -> int:
    return _run_resource_info_command(repo, proto, repo_url, **kwargs)


def _run_repo_info_command(
        repo: GenomicResourceRepo,
        proto: ReadWriteRepositoryProtocol,
        **kwargs: str | bool | int) -> int:
    status = _run_repo_stats_command(repo, proto, **kwargs)

    dry_run = cast(bool, kwargs.get("dry_run", False))
    if dry_run:
        return status

    proto.build_index_info(repository_template)  # type: ignore
    for res in proto.get_all_resources():
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


def _run_resource_info_command(
        repo: GenomicResourceRepo,
        proto: ReadWriteRepositoryProtocol,
        repo_url: str,
        **kwargs: str | int | bool) -> int:
    status = _run_resource_stats_command(
        repo, proto, repo_url, **kwargs)

    dry_run = cast(bool, kwargs.get("dry_run", False))
    if dry_run:
        return status

    res = _find_resource(proto, repo_url, **kwargs)
    if res is None:
        logger.error("resource not found...")
        return 1
    _do_resource_info_command(repo, proto, res)

    return 0


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

    repo_url = args.repository
    if repo_url is None:
        repo_url = find_directory_with_a_file(GR_CONTENTS_FILE_NAME)
        if repo_url is None:
            repo_url = find_directory_with_a_file(GR_CONTENTS_FILE_NAME[:-5])
        if repo_url is None:
            logger.error(
                "Can't find repository starting from: %s", os.getcwd())
            sys.exit(1)
        repo_url = str(repo_url)
        print(f"working with repository: {repo_url}")

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

    repo = build_genomic_resource_repository(definition=grr_definition)

    proto = _create_proto(repo_url, args.extra_args)
    if command == "list":
        _run_list_command(proto, args)
        return

    if not isinstance(proto, ReadWriteRepositoryProtocol):
        raise TypeError(
            f"resource management works with RW protocols; "
            f"{proto.proto_id} ({proto.scheme}) is read only")

    if command in {"repo-manifest", "repo-stats", "repo-info", "repo-repair"}:
        status = 0
        try:
            if command == "repo-manifest":
                status = _run_repo_manifest_command(proto, **vars(args))
            elif command == "repo-stats":
                status = _run_repo_stats_command(repo, proto, **vars(args))
            elif command == "repo-info":
                status = _run_repo_info_command(repo, proto, **vars(args))
            elif command == "repo-repair":
                status = _run_repo_repair_command(repo, proto, **vars(args))
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
        try:
            if command == "resource-manifest":
                status = _run_resource_manifest_command(
                    proto, repo_url, **vars(args))
            elif command == "resource-stats":
                status = _run_resource_stats_command(
                    repo, proto, repo_url, **vars(args))
            elif command == "resource-info":
                status = _run_resource_info_command(
                    repo, proto, repo_url, **vars(args))
            elif command == "resource-repair":
                status = _run_resource_repair_command(
                    repo, proto, repo_url, **vars(args))
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

    else:
        logger.error(
            "Unknown command %s. The known commands are index, "
            "list and histogram", command)
        sys.exit(1)


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


repository_template = Template("""
<html>
 <head>
    <style>
        th {
            background: lightgray;
        }
        td, th {
            border: 1px solid black;
            padding: 5px;
        }
        table {
            border: 3px inset;
            max-width: 60%;
        }
        table, td, th {
            border-collapse: collapse;
        }
        .meta-div {
            max-height: 250px;
            overflow: scroll;
        }
        .nowrap {
            white-space: nowrap
        }
    </style>
 </head>
 <body>
     <table>
        <thead>
            <tr>
                <th>Type</th>
                <th>ID</th>
                <th>Version</th>
                <th>Number of files</th>
                <th>Size in bytes (total)</th>
                <th>Summary</th>
            </tr>
        </thead>
        <tbody>
            {%- for key, value in data.items() recursive%}
            <tr>
                <td class="nowrap">{{value['type']}}</td>
                <td class="nowrap">
                    <a href='{{key}}/index.html'>{{key}}</a>
                </td>
                <td class="nowrap">{{value['res_version']}}</td>
                <td class="nowrap">{{value['res_files']}}</td>
                <td class="nowrap">{{value['res_size']}}</td>
                <td class="nowrap">{{value['res_summary']}}</td>
            </tr>
            {%- endfor %}
        </tbody>
     </table>
 </body>
</html>
""")
