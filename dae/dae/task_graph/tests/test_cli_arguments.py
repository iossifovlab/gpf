# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import argparse
from typing import Optional

import pytest

from dae.task_graph import TaskGraphCli


@pytest.mark.parametrize("argv,jobs", [
    (["-j", "1"], 1),
    ([], None),
    (["-j", "100"], 100),
    (["--jobs", "1"], 1),
    (["--jobs", "100"], 100),
])
def test_cli_args_jobs(argv: list[str], jobs: Optional[int]) -> None:
    parser = argparse.ArgumentParser(description="test_basic")
    TaskGraphCli.add_arguments(parser)
    args = parser.parse_args(argv)

    assert args.jobs == jobs


@pytest.mark.parametrize("argv,command", [
    ([], "run"),
    (["run"], "run"),
    (["list"], "list"),
    (["status"], "status"),
])
def test_cli_args_command(argv: list[str], command: str) -> None:
    parser = argparse.ArgumentParser(description="test_basic")
    TaskGraphCli.add_arguments(parser)
    args = parser.parse_args(argv)

    assert args.command == command


@pytest.mark.parametrize("argv,name", [
    ([], None),
    (["-N", "abc"], "abc"),
    (["--dcn", "abc"], "abc"),
    (["--dask-cluster-name", "abc"], "abc"),
])
def test_cli_args_dask_cluster_name(
        argv: list[str], name: Optional[str]) -> None:
    parser = argparse.ArgumentParser(description="test_basic")
    TaskGraphCli.add_arguments(parser)
    args = parser.parse_args(argv)

    assert args.dask_cluster_name == name


@pytest.mark.parametrize("argv,filename", [
    ([], None),
    (["-c", "abc.yaml"], "abc.yaml"),
    (["--dccf", "abc.yaml"], "abc.yaml"),
    (["--dask-cluster-config-file", "abc.yaml"], "abc.yaml"),
])
def test_cli_args_dask_cluster_config_file(
        argv: list[str], filename: Optional[str]) -> None:
    parser = argparse.ArgumentParser(description="test_basic")
    TaskGraphCli.add_arguments(parser)
    args = parser.parse_args(argv)

    assert args.dask_cluster_config_file == filename


@pytest.mark.parametrize("argv,task_ids", [
    ([], None),
    (["--task-ids", "a"], ["a"]),
    (["--task-ids", "a", "b"], ["a", "b"]),
    (["--task-ids", "a", "b", "c"], ["a", "b", "c"]),
    (["-t", "a"], ["a"]),
    (["-t", "a", "b"], ["a", "b"]),
    (["-t", "a", "b", "c"], ["a", "b", "c"]),
])
def test_cli_args_task_ids(
        argv: list[str], task_ids: Optional[list[str]]) -> None:
    parser = argparse.ArgumentParser(description="test_basic")
    TaskGraphCli.add_arguments(parser)
    args = parser.parse_args(argv)

    assert args.task_ids == task_ids


@pytest.mark.parametrize("argv,keep_going", [
    ([], False),
    (["--keep-going"], True),
])
def test_cli_args_keep_going(argv: list[str], keep_going: bool) -> None:
    parser = argparse.ArgumentParser(description="test_basic")
    TaskGraphCli.add_arguments(parser)
    args = parser.parse_args(argv)

    assert args.keep_going == keep_going


@pytest.mark.parametrize("force_mode,argv,force", [
    ("optional", [], False),
    ("optional", ["--force"], True),
    ("always", [], None),
])
def test_cli_args_force(
        force_mode: str, argv: list[str], force: Optional[bool]) -> None:
    parser = argparse.ArgumentParser(description="test_basic")
    TaskGraphCli.add_arguments(parser, force_mode=force_mode)
    args = vars(parser.parse_args(argv))

    assert args.get("force") == force


@pytest.mark.parametrize("default_task_status_dir, argv,task_status_dir", [
    (".", [], "."),
    ("/a/b/c", [], "/a/b/c"),
    (".", ["-d", ".status"], ".status"),
    (".", ["--tsd", ".status"], ".status"),
    (".", ["--task-status-dir", ".status"], ".status"),
])
def test_cli_args_task_status_dir(
        default_task_status_dir: str, argv: list[str],
        task_status_dir: str) -> None:
    parser = argparse.ArgumentParser(description="test_basic")
    TaskGraphCli.add_arguments(
        parser, default_task_status_dir=default_task_status_dir)
    args = parser.parse_args(argv)

    assert args.task_status_dir == task_status_dir
