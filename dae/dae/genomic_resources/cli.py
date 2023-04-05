"""Provides CLI for management of genomic resources repositories."""
import os
import sys
import logging
import argparse
import pathlib
import copy

from typing import Dict, Union
from urllib.parse import urlparse

import yaml

from cerberus.schema import SchemaError

from jinja2 import Template

from dae.utils.helpers import convert_size

from dae.task_graph.cli_tools import TaskGraphCli
from dae.utils.fs_utils import find_directory_with_a_file
from dae.task_graph.graph import TaskGraph
from dae.__version__ import VERSION, RELEASE
from dae.genomic_resources.repository import \
    GR_CONF_FILE_NAME, \
    GR_CONTENTS_FILE_NAME, \
    GenomicResource, \
    GenomicResourceRepo, \
    ReadOnlyRepositoryProtocol, \
    ReadWriteRepositoryProtocol, \
    ManifestEntry, \
    parse_resource_id_version, \
    version_tuple_to_string
from dae.genomic_resources.cached_repository import \
    GenomicResourceCachedRepo

from dae.utils.verbosity_configuration import VerbosityConfiguration

from dae.genomic_resources.fsspec_protocol import build_fsspec_protocol
from dae.genomic_resources.repository_factory import \
    build_genomic_resource_repository, get_default_grr_definition, \
    load_definition_file

from dae.genomic_resources import get_resource_implementation_builder


logger = logging.getLogger("grr_manage")


def _add_repository_resource_parameters_group(parser, use_resource=True):

    group = parser.add_argument_group(title="Repository/Resource")
    group.add_argument(
        "-R", "--repository", type=str,
        default=None,
        help="URL to the genomic resources repository. If not specified "
        "the tool assumes a local file system repository and starts looking "
        "for .CONTENTS file from the current working directory up to the root "
        "directory. If found the directory is assumed for root repository "
        "directory; otherwise error is reported.")
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
        "neccessary to pass additional `endpoint-url` argument."
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


def _add_dry_run_and_force_parameters_group(parser):
    group = parser.add_argument_group(title="Force/Dry run")
    group.add_argument(
        "-n", "--dry-run", default=False, action="store_true",
        help="only checks if the manifest update is needed whithout "
        "actually updating it")
    group.add_argument(
        "-f", "--force", default=False,
        action="store_true",
        help="ignore resource state and rebuild manifest")


def _add_dvc_parameters_group(parser):
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


def _add_hist_parameters_group(parser):
    group = parser.add_argument_group(title="Statistics")
    group.add_argument(
        "--region-size", type=int, default=300_000_000,
        help="Region size to use for splitting statistics calculation into "
        "tasks")


def _configure_list_subparser(subparsers):
    parser = subparsers.add_parser("list", help="List a GR Repo")
    parser.add_argument("--hr", default=False, action="store_true", help="Projects the size in human-readable format.")
    _add_repository_resource_parameters_group(parser, use_resource=False)
    VerbosityConfiguration.set_argumnets(parser)


def _run_list_command(
        proto: Union[ReadOnlyRepositoryProtocol, GenomicResourceRepo], args):

    for res in proto.get_all_resources():
        res_size = sum(fs for _, fs in res.get_manifest().get_files())

        files_msg = f"{len(list(res.get_manifest().get_files())):2d}"
        if isinstance(proto, GenomicResourceCachedRepo):
            files_msg = f"{len(proto.get_resource_cached_files(res.get_id())):2d}/{files_msg}"

        res_size_msg = convert_size(res_size) if hasattr(args, 'hr') and args.hr is True else res_size
        print(
            f"{res.get_type():20} {res.get_version_str():7s} "
            f"{files_msg} {res_size_msg:12} "
            f"{proto.repo_id if isinstance(proto, GenomicResourceRepo) else proto.get_id()} "
            f"{res.get_id()}")


def _configure_repo_init_subparser(subparsers):
    parser = subparsers.add_parser(
        "repo-init", help="Initialize a directory to turn it into a GRR")

    _add_repository_resource_parameters_group(parser, use_resource=False)
    _add_dry_run_and_force_parameters_group(parser)
    VerbosityConfiguration.set_argumnets(parser)


def _run_repo_init_command(**kwargs):
    repository = kwargs.get("repository")
    if repository is None:
        repo_url = find_directory_with_a_file(GR_CONTENTS_FILE_NAME)
    else:
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


def _configure_repo_manifest_subparser(subparsers):
    parser = subparsers.add_parser(
        "repo-manifest", help="Create/update manifests for whole GRR")

    _add_repository_resource_parameters_group(parser, use_resource=False)
    _add_dry_run_and_force_parameters_group(parser)
    _add_dvc_parameters_group(parser)
    VerbosityConfiguration.set_argumnets(parser)


def _configure_resource_manifest_subparser(subparsers):
    parser = subparsers.add_parser(
        "resource-manifest", help="Create/update manifests for a resource")

    _add_repository_resource_parameters_group(parser)
    _add_dry_run_and_force_parameters_group(parser)
    _add_dvc_parameters_group(parser)
    VerbosityConfiguration.set_argumnets(parser)


def _configure_repo_stats_subparser(subparsers):
    parser = subparsers.add_parser(
        "repo-stats",
        help="Build the statistics for a resource")

    _add_repository_resource_parameters_group(parser, use_resource=False)
    _add_dry_run_and_force_parameters_group(parser)
    _add_dvc_parameters_group(parser)
    _add_hist_parameters_group(parser)
    VerbosityConfiguration.set_argumnets(parser)

    TaskGraphCli.add_arguments(parser, use_commands=False, force_mode="always")


def _configure_resource_stats_subparser(subparsers):
    parser = subparsers.add_parser(
        "resource-stats",
        help="Build the statistics for a resource")

    _add_repository_resource_parameters_group(parser)
    _add_dry_run_and_force_parameters_group(parser)
    _add_dvc_parameters_group(parser)
    _add_hist_parameters_group(parser)
    VerbosityConfiguration.set_argumnets(parser)

    TaskGraphCli.add_arguments(parser, use_commands=False, force_mode="always")


def _configure_repo_repair_subparser(subparsers):
    parser = subparsers.add_parser(
        "repo-repair",
        help="Update/rebuild manifest and histograms whole GRR")
    _add_repository_resource_parameters_group(parser, use_resource=False)
    _add_dry_run_and_force_parameters_group(parser)
    _add_dvc_parameters_group(parser)
    _add_hist_parameters_group(parser)
    VerbosityConfiguration.set_argumnets(parser)

    TaskGraphCli.add_arguments(parser, use_commands=False, force_mode="always")


def _configure_resource_repair_subparser(subparsers):
    parser = subparsers.add_parser(
        "resource-repair",
        help="Update/rebuild manifest and histograms for a resource")
    _add_repository_resource_parameters_group(parser)
    _add_dry_run_and_force_parameters_group(parser)
    _add_dvc_parameters_group(parser)
    _add_hist_parameters_group(parser)
    VerbosityConfiguration.set_argumnets(parser)

    TaskGraphCli.add_arguments(parser, use_commands=False, force_mode="always")


def _configure_repo_info_subparser(subparsers):
    parser = subparsers.add_parser(
        "repo-info", help="Build the index.html for the whole GRR"
    )
    _add_repository_resource_parameters_group(parser)
    VerbosityConfiguration.set_argumnets(parser)

    TaskGraphCli.add_arguments(parser, use_commands=False, force_mode="always")


def _configure_resource_info_subparser(subparsers):
    parser = subparsers.add_parser(
        "resource-info", help="Build the index.html for the specific resource"
    )
    _add_repository_resource_parameters_group(parser)
    VerbosityConfiguration.set_argumnets(parser)

    TaskGraphCli.add_arguments(parser, use_commands=False, force_mode="always")


def collect_dvc_entries(
        proto: ReadWriteRepositoryProtocol,
        res: GenomicResource) -> Dict[str, ManifestEntry]:
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


def _do_resource_manifest_command(proto, res, dry_run, force, use_dvc):
    prebuild_entries = {}
    if use_dvc:
        prebuild_entries = collect_dvc_entries(proto, res)

    manifest_update = proto.check_update_manifest(res, prebuild_entries)
    if not bool(manifest_update):
        logger.info(
            "manifest of <%s> is up to date",
            res.get_genomic_resource_id_version())
    else:
        msg = \
            f"manifest of " \
            f"<{res.get_genomic_resource_id_version()}> " \
            f"should be updated; " \
            f"entries to update in manifest " \
            f"{sorted(manifest_update.entries_to_update)}"
        if manifest_update.entries_to_delete:
            msg = f"{msg}; " \
                f"entries to delete from manifest " \
                f"{sorted(manifest_update.entries_to_delete)}"
        logger.info(msg)

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


def _run_repo_manifest_command(proto, **kwargs):
    dry_run = kwargs.get("dry_run", False)
    force = kwargs.get("force", False)
    use_dvc = kwargs.get("use_dvc", True)

    if dry_run and force:
        logger.warning("please choose one of 'dry_run' and 'force' options")
        return {}

    updates_needed = {}
    for res in proto.get_all_resources():
        updates_needed[res.resource_id] = _do_resource_manifest_command(
            proto, res, dry_run, force, use_dvc
        )

    if not dry_run:
        proto.build_content_file()

    return updates_needed


def _find_resource(proto, repo_url, **kwargs):
    resource_id = kwargs.get("resource")
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


def _run_resource_manifest_command(proto, repo_url, **kwargs):
    dry_run = kwargs.get("dry_run", False)
    force = kwargs.get("force", False)
    use_dvc = kwargs.get("use_dvc", True)

    if dry_run and force:
        logger.warning("please choose one of 'dry_run' and 'force' options")
        return False
    res = _find_resource(proto, repo_url, **kwargs)
    if res is None:
        logger.error("resource not found...")
        return False
    return _do_resource_manifest_command(proto, res, dry_run, force, use_dvc)


def _read_stats_hash(proto, implementation):
    res = implementation.resource
    stats = implementation.get_statistics()
    stats_dir = None
    if stats is not None:
        stats_dir = stats.get_statistics_folder()
    if stats is None or stats_dir is None:
        logger.warning("Couldn't read stats hash for %s", res.resource_id)
        return False
    if not proto.file_exists(res, f"{stats_dir}/stats_hash"):
        return None
    with proto.open_raw_file(
        res, f"{stats_dir}/stats_hash", mode="rb"
    ) as infile:
        return infile.read()


def _store_stats_hash(proto, resource):
    impl = build_resource_implementation(resource)
    stats = impl.get_statistics()
    stats_dir = None
    if stats is not None:
        stats_dir = stats.get_statistics_folder()
    if stats is None or stats_dir is None:
        logger.warning(
            "Couldn't store stats hash for %s", resource.resource_id
        )
        return False
    with proto.open_raw_file(
        resource, f"{stats_dir}/stats_hash", mode="wb"
    ) as outfile:
        stats_hash = impl.calc_statistics_hash()
        outfile.write(stats_hash)
    return True


def _collect_impl_stats_tasks(  # pylint: disable=too-many-arguments
        graph, proto, impl, grr, dry_run, force, use_dvc, region_size):

    tasks = impl.add_statistics_build_tasks(graph, region_size=region_size, grr=grr)

    graph.create_task(
        f"{impl.resource.resource_id}_store_stats_hash",
        _store_stats_hash,
        [proto, impl.resource],
        tasks
    )

    graph.create_task(
        f"{impl.resource.resource_id}_manifest_rebuild",
        _do_resource_manifest_command,
        [proto, impl.resource, dry_run, force, use_dvc],
        tasks
    )


def _stats_need_rebuild(proto, impl):
    """Check if an implementation's stats need rebuilding."""
    current_hash = impl.calc_statistics_hash()

    stored_hash = _read_stats_hash(proto, impl)

    if stored_hash is None:
        logger.info(
            "No hash stored for <%s>, need update",
            impl.resource.resource_id
        )
        return True

    if stored_hash != current_hash:
        logger.info(
            "Stored hash for <%s> is outdated, need update",
            impl.resource.resource_id
        )
        return True

    logger.info(
        "<%s> statistics hash is up to date", impl.resource.resource_id
    )
    return False


def _run_repo_stats_command(repo, proto, **kwargs):
    updates_needed = _run_repo_manifest_command(proto, **kwargs)
    dry_run = kwargs.get("dry_run", False)
    force = kwargs.get("force", False)
    use_dvc = kwargs.get("use_dvc", True)
    region_size = kwargs.get("region_size", 3_000_000)
    if dry_run and force:
        logger.warning("please choose one of 'dry_run' and 'force' options")
        return

    graph = TaskGraph()

    for res in proto.get_all_resources():
        if updates_needed[res.resource_id]:
            logger.info(
                "Manifest of <%s> needs update, cannot check statistics",
                res.resource_id
            )
            continue
        impl = build_resource_implementation(res)
        needs_rebuild = _stats_need_rebuild(proto, impl)
        if (force or needs_rebuild) and not dry_run:
            _collect_impl_stats_tasks(
                graph, proto, impl, repo, dry_run, force, use_dvc, region_size)
        elif dry_run and needs_rebuild:
            logger.info("Statistics of <%s> need update", res.resource_id)

    if not dry_run and len(graph.tasks) > 0:
        modified_kwargs = copy.copy(kwargs)
        modified_kwargs["command"] = "run"
        TaskGraphCli.process_graph(
            graph, force_mode="always", **modified_kwargs)

    if not dry_run:
        proto.build_content_file()


def _run_resource_stats_command(repo, proto, repo_url, **kwargs):
    needs_update = _run_resource_manifest_command(proto, repo_url, **kwargs)
    dry_run = kwargs.get("dry_run", False)
    force = kwargs.get("force", False)
    use_dvc = kwargs.get("use_dvc", True)
    region_size = kwargs.get("region_size", 3_000_000)
    res = _find_resource(proto, repo_url, **kwargs)
    if needs_update:
        logger.info(
            "Manifest of <%s> needs update, cannot check statistics",
            res.resource_id
        )
        return
    if dry_run and force:
        logger.warning("please choose one of 'dry_run' and 'force' options")
        return

    if res is None:
        logger.error("unable to find resource...")
        return

    impl = build_resource_implementation(res)

    needs_rebuild = _stats_need_rebuild(proto, impl)

    if dry_run and needs_rebuild:
        logger.info("Statistics of <%s> need update", res.resource_id)
        return

    if (force or needs_rebuild) and not dry_run:
        graph = TaskGraph()
        _collect_impl_stats_tasks(
            graph, proto, impl, repo, dry_run, force, use_dvc, region_size)
        if len(graph.tasks) == 0:
            return
        modified_kwargs = copy.copy(kwargs)
        modified_kwargs["command"] = "run"
        TaskGraphCli.process_graph(
            graph, force_mode="always", **modified_kwargs
        )


def _run_repo_repair_command(repo, proto, **kwargs):
    _run_repo_info_command(repo, proto, **kwargs)


def _run_resource_repair_command(repo, proto, repo_url, **kwargs):
    _run_resource_info_command(repo, proto, repo_url, **kwargs)


def _run_repo_info_command(repo, proto, **kwargs):
    _run_repo_stats_command(repo, proto, **kwargs)
    proto.build_index_info(repository_template)

    for res in proto.get_all_resources():
        try:
            _do_resource_info_command(proto, res)
        except ValueError as err:
            logger.error(
                "Failed to generate repo index for %s\n%s",
                res.resource_id,
                err
            )
        except SchemaError as err:
            logger.error(
                "Resource %s has an invalid configuration\n%s",
                res.resource_id,
                err
            )
        except BaseException as err:  # pylint: disable=broad-except
            logger.error(
                "Failed to load %s\n%s",
                res.resource_id,
                err
            )


def build_resource_implementation(res):
    builder = get_resource_implementation_builder(res.get_type())
    return builder(res)


def _do_resource_info_command(proto, res):
    implementation = build_resource_implementation(res)

    with proto.open_raw_file(res, "index.html", mode="wt") as outfile:
        content = implementation.get_info()
        outfile.write(content)


def _run_resource_info_command(repo, proto, repo_url, **kwargs):
    _run_resource_stats_command(repo, proto, repo_url, **kwargs)
    res = _find_resource(proto, repo_url, **kwargs)
    if res is None:
        logger.error("resource not found...")
        return

    _do_resource_info_command(proto, res)


def cli_manage(cli_args=None):
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
    VerbosityConfiguration.set_argumnets(parser)

    commands_parser = parser.add_subparsers(
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
        print(f"GPF version: {VERSION} ({RELEASE})")
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
            logger.error(
                "Can't find repository starting from: %s", os.getcwd())
            sys.exit(1)
        repo_url = str(repo_url)
        print(f"working with repository: {repo_url}")

    extra_definition_path = args.grr
    if extra_definition_path:
        if not os.path.exists(extra_definition_path):
            raise FileNotFoundError(
                f"Definition {extra_definition_path} not found!"
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
                "directory": repo_url
            },
            extra_definition
        ]
    }

    repo = build_genomic_resource_repository(definition=grr_definition)

    proto = _create_proto(repo_url, args.extra_args)
    if command == "list":
        _run_list_command(proto, args)
        return

    if not isinstance(proto, ReadWriteRepositoryProtocol):
        raise ValueError(
            f"resource management works with RW protocols; "
            f"{proto.proto_id} ({proto.scheme}) is read only")

    if command == "repo-manifest":
        _run_repo_manifest_command(proto, **vars(args))
    elif command == "resource-manifest":
        _run_resource_manifest_command(proto, repo_url, **vars(args))
    elif command == "repo-stats":
        _run_repo_stats_command(repo, proto, **vars(args))
    elif command == "resource-stats":
        _run_resource_stats_command(repo, proto, repo_url, **vars(args))
    elif command == "repo-info":
        _run_repo_info_command(repo, proto, **vars(args))
    elif command == "resource-info":
        _run_resource_info_command(repo, proto, repo_url, **vars(args))
    elif command == "repo-repair":
        _run_repo_repair_command(repo, proto, **vars(args))
    elif command == "resource-repair":
        _run_resource_repair_command(repo, proto, repo_url, **vars(args))
    else:
        logger.error(
            "Unknown command %s. The known commands are index, "
            "list and histogram", command)
        sys.exit(1)


def _create_proto(repo_url, extra_args: str = ""):
    url = urlparse(repo_url)

    if url.scheme in {"file", ""} and not os.path.isabs(repo_url):
        repo_url = os.path.abspath(repo_url)

    kwargs: Dict[str, str] = {}
    if extra_args:
        parsed = [tuple(a.split("=")) for a in extra_args.split(",")]
        kwargs = {p[0]: p[1] for p in parsed}

    proto = build_fsspec_protocol(
        proto_id="manage", root_url=repo_url, **kwargs)
    return proto


def cli_browse(cli_args=None):
    """Provide CLI for repository browsing."""
    desc = "Genomic Resource Repository Browse Tool"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "--version", action="store_true", default=False,
        help="Prints GPF version and exists.")
    VerbosityConfiguration.set_argumnets(parser)

    group = parser.add_argument_group(title="Repository/Resource")
    group.add_argument(
        "-g", "--grr", type=str,
        default=None,
        help="path to GRR definition file.")

    parser.add_argument("--hr", default=False, action="store_true", help="Projects the size in human-readable format.")

    if cli_args is None:
        cli_args = sys.argv[1:]
    args = parser.parse_args(cli_args)
    VerbosityConfiguration.set(args)

    if args.version:
        print(f"GPF version: {VERSION} ({RELEASE})")
        sys.exit(0)
    repo = build_genomic_resource_repository(file_name=args.grr)
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
                <th>Meta</th>
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
                <td>
                    <div class="meta-div">
                        {{value.get('meta', 'N/A')}}
                    </div>
                </td>
            </tr>
            {%- endfor %}
        </tbody>
     </table>
 </body>
</html>
""")
