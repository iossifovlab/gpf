# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import argparse


from dae.task_graph import TaskGraph
from dae.task_graph import TaskGraphCli


def test_basic_defalt_executor():
    parser = argparse.ArgumentParser(description="test_basic")
    TaskGraphCli.add_arguments(parser)
    args = parser.parse_args([])

    empty_graph = TaskGraph()
    TaskGraphCli.process_graph(empty_graph, args)


def test_basic_sequential_executor():
    parser = argparse.ArgumentParser(description="test_basic")
    TaskGraphCli.add_arguments(parser)
    args = parser.parse_args(["-j", "1"])

    empty_graph = TaskGraph()
    TaskGraphCli.process_graph(empty_graph, args)


def test_force_alwasy():
    parser = argparse.ArgumentParser(description="test_basic")
    TaskGraphCli.add_arguments(parser, force_mode="always")
    args = parser.parse_args([])

    assert "force" not in vars(args)
    assert "task_status_dir" not in vars(args)


def test_force_optional():
    parser = argparse.ArgumentParser(description="test_basic")
    TaskGraphCli.add_arguments(parser, force_mode="optional",
                               default_task_status_dir="gosho")

    args = parser.parse_args([])
    assert not args.force
    assert args.task_status_dir == "gosho"

    args = parser.parse_args(["-tsd", "pesho"])
    assert not args.force
    assert args.task_status_dir == "pesho"

    args = parser.parse_args(["-f"])
    assert args.force
    assert args.task_status_dir == "gosho"
