import argparse

from dae.task_graph.cli_tools import add_arguments
from dae.task_graph.cli_tools import process_graph
from dae.task_graph.graph import TaskGraph


def test_basic_defalt_executor():
    parser = argparse.ArgumentParser(description="test_basic")
    add_arguments(parser)
    args = parser.parse_args([])

    empty_graph = TaskGraph()
    process_graph(args, empty_graph)


def test_basic_sequential_executor():
    parser = argparse.ArgumentParser(description="test_basic")
    add_arguments(parser)
    args = parser.parse_args(["-j", "1"])

    empty_graph = TaskGraph()
    process_graph(args, empty_graph)


