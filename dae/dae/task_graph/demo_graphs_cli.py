import argparse
import sys
import time
from typing import Optional

from dae.task_graph import TaskGraphCli
from dae.task_graph.graph import TaskGraph
from dae.utils.verbosity_configuration import VerbosityConfiguration


def _build_graph_a(graph_params: Optional[list[str]]) -> TaskGraph:
    task_graph = TaskGraph()

    num_of_parts, parts_sleep, summary_sleep = "10", "2", "2"

    if graph_params:
        if len(graph_params) != 3:
            raise ValueError(
                "The graph A needs three parameters: "
                "<number of parts>, <seconds for parts>, "
                "<seconds for summary>")
        num_of_parts, parts_sleep, summary_sleep = graph_params
    print(
        f"Bulding graph A with {num_of_parts} parts, "
        f"{parts_sleep} seconds for each parts, and "
        f"{summary_sleep} secoconds for the summary")

    def task_part() -> None:
        time.sleep(float(parts_sleep))

    def task_summary() -> None:
        time.sleep(float(summary_sleep))

    parts = [task_graph.create_task(
        f"part {p}", task_part, [], [])
        for p in range(int(num_of_parts))]
    task_graph.create_task("summary", task_summary, [], parts)
    return task_graph


def _build_graph_d(graph_params: Optional[list[str]]) -> TaskGraph:
    task_graph = TaskGraph()

    num_of_clicks, num_of_parts, parts_sleep, summary_sleep = \
        "5", "10", "2", "2"

    if graph_params:
        if len(graph_params) != 4:
            raise ValueError(
                "The graph D needs three parameters: "
                "<number of parts>, <seconds for parts>, "
                "<seconds for summary>")
        num_of_clicks, num_of_parts, parts_sleep, summary_sleep = graph_params
    print(
        f"Bulding graph D with {num_of_clicks} clicks, {num_of_parts} parts, "
        f"{parts_sleep} seconds for each parts, and "
        f"{summary_sleep} secoconds for the summary")

    def task_part() -> None:
        time.sleep(float(parts_sleep))

    def task_summary() -> None:
        time.sleep(float(summary_sleep))

    for click in range(int(num_of_clicks)):
        parts = [task_graph.create_task(
            f"part {click}:{p}", task_part, [], [])
            for p in range(int(num_of_parts))]
        task_graph.create_task(f"summary {click}", task_summary, [], parts)
    return task_graph


def _build_graph_b(graph_params: Optional[list[str]]) -> TaskGraph:
    task_graph = TaskGraph()

    num_of_parts, parts_sleep, summary_sleep = "2", "5", "10"

    if graph_params:
        if len(graph_params) != 3:
            raise ValueError(
                "The graph B needs three parameters: "
                "<number of parts>, <seconds for parts>, "
                "<seconds for summary>")
        num_of_parts, parts_sleep, summary_sleep = graph_params
    print(
        f"Bulding graph A with {num_of_parts} parts, "
        f"{parts_sleep} seconds for each parts, and "
        f"{summary_sleep} secoconds for the summary")

    def task_part() -> str:
        time.sleep(float(parts_sleep))
        return 1000 * "B"

    def task_summary(*args: str) -> str:
        time.sleep(float(summary_sleep))
        if len(args) <= 5:
            return "b".join(args)
        return "c".join(args[:5])

    parts = [task_graph.create_task(
        f"part {p}", task_part, [], [])
        for p in range(int(num_of_parts))]
    task_graph.create_task("summary", task_summary, parts, parts)
    return task_graph


def _build_graph_c(graph_params: Optional[list[str]]) -> TaskGraph:
    task_graph = TaskGraph()

    num_of_parts, parts_sleep, summary_sleep = "2", "5", "10"

    if graph_params:
        if len(graph_params) != 3:
            raise ValueError(
                "The graph C needs three parameters: "
                "<number of parts>, <sleep for parts>, "
                "<sleep for summary>")
        num_of_parts, parts_sleep, summary_sleep = graph_params
    print(
        f"Bulding graph C with {num_of_parts} parts, "
        f"{parts_sleep} seconds sleep for each parts, and "
        f"{summary_sleep} secoconds sleep for the summary")

    def task_part(*_args: str) -> str:
        time.sleep(float(parts_sleep))
        return 1000 * "B"

    def task_summary(*args: str) -> str:
        time.sleep(float(summary_sleep))
        if len(args) <= 5:
            return "b".join(args)
        return "c".join(args[:5])

    parts = [
        task_graph.create_task(f"part {p}", task_part, [], [])
        for p in range(int(num_of_parts))
    ]
    summary = task_graph.create_task("summary", task_summary, parts, parts)
    parts2 = [
        task_graph.create_task(f"part2 {p}", task_part, [summary], [summary])
        for p in range(int(num_of_parts))
    ]
    task_graph.create_task("summary2", task_summary, parts2, parts2)
    return task_graph


def build_demo_graph(graph_type: str,
                     graph_params: Optional[list[str]]) -> TaskGraph:
    """Build a demo graph."""
    if graph_type == "A":
        return _build_graph_a(graph_params)

    if graph_type == "B":
        return _build_graph_b(graph_params)

    if graph_type == "C":
        return _build_graph_c(graph_params)

    if graph_type == "D":
        return _build_graph_d(graph_params)

    raise ValueError(f"Unknown graph <{graph_type}>")


def main(argv: Optional[list[str]] = None) -> None:
    """Entry point for the demo script."""
    parser = argparse.ArgumentParser(description="test_basic")

    parser.add_argument("graph", type=str, help="Demo graph",
                        default="A", nargs="?")
    VerbosityConfiguration.set_arguments(parser)

    parser.add_argument("--graph-params", "-gp", type=str, nargs="+")

    TaskGraphCli.add_arguments(parser)

    if argv is None:
        argv = sys.argv[1:]
    args = parser.parse_args(argv)
    VerbosityConfiguration.set(args)
    graph = build_demo_graph(args.graph, args.graph_params)
    TaskGraphCli.process_graph(graph, **vars(args))
