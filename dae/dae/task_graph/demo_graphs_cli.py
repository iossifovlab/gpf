import argparse
import sys
import time
from typing import Optional, List

from dae.task_graph import TaskGraphCli
# TaskGraphCli.add_arumgetts
# TaksGraphClie.process_graph
from dae.task_graph.graph import TaskGraph


def build_demo_graph(graph_type: str,
                     graph_params: Optional[List[str]]) -> TaskGraph:
    """Build a demo graph."""
    task_graph = TaskGraph()

    if graph_type == "A":
        NP, SP, SS = 10, 1, 1  # pylint: disable=invalid-name

        if graph_params:
            if len(graph_params) != 3:

                raise Exception("The graph A needs three parameters: "
                                "<number of parts>, <seconds for parts>, "
                                "<seconds for summary>")
            NP, SP, SS = map(int, graph_params)  # pylint: disable=invalid-name
        print(f"Bulding graph A with {NP} parts, {SP} seconds for "
              f"each parts, and {SS} secoconds for the summary")

        parts = [task_graph.create_task(
            f"part {p}", lambda: time.sleep(SP), [], []) for p in range(NP)]
        task_graph.create_task("summary", lambda: time.sleep(SS), [], parts)
    else:
        raise Exception("Unknown graph")

    return task_graph


def main(argv=None):
    """Entry point for the demo script."""
    parser = argparse.ArgumentParser(description="test_basic")

    parser.add_argument("graph", type=str, help="Demo graph",
                        default="A", nargs="?")
    parser.add_argument("--graph_params", "-gp", type=str, nargs="+")

    TaskGraphCli.add_arguments(parser)

    args = parser.parse_args(argv or sys.argv[1:])

    empty_graph = build_demo_graph(args.graph, args.graph_params)
    TaskGraphCli.process_graph(args, empty_graph)
