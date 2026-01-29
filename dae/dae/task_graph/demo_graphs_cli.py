import argparse
import random
import sys
import time

from dae.task_graph.cli_tools import TaskGraphCli
from dae.task_graph.graph import TaskGraph
from dae.utils.verbosity_configuration import VerbosityConfiguration


def timeout(seconds: str) -> float:
    t = float(seconds)
    return max(random.gauss(t, 0.7 * t), 0.1)


def task_part(seconds: str) -> str:
    time.sleep(timeout(seconds))
    return 2_000 * "P"


def task_summary(seconds: str) -> None:
    time.sleep(timeout(seconds))


def task_part_b(seconds: str) -> str:
    time.sleep(timeout(seconds))
    return 2_000 * "B"


def task_summary_b(seconds: str, *args: str) -> str:
    time.sleep(timeout(seconds))
    if len(args) <= 5:
        return "b".join(args)
    return "c".join(args[:5])


def task_part_c(seconds: str, *_args: str) -> str:
    time.sleep(timeout(seconds))
    return 2_000 * "C"


def task_summary_c(seconds: str, *args: str) -> str:
    time.sleep(timeout(seconds))
    if len(args) <= 5:
        return "b".join(args)
    return "c".join(args[:5])


def _build_graph_a(graph_params: list[str] | None) -> TaskGraph:
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

    parts = [task_graph.create_task(
        f"part {p}", task_part, args=[parts_sleep], deps=[])
        for p in range(int(num_of_parts))]
    task_graph.create_task(
        "summary", task_summary, args=[summary_sleep], deps=parts)
    return task_graph


def _build_graph_d(graph_params: list[str] | None) -> TaskGraph:
    task_graph = TaskGraph()

    num_of_clicks, num_of_parts, parts_sleep, summary_sleep = \
        "5", "10", "2", "2"

    if graph_params:
        if len(graph_params) != 4:
            raise ValueError(
                "The graph D needs four parameters: "
                "<number of clicks>, <number of parts>, "
                "<seconds for parts>, <seconds for summary>")
        num_of_clicks, num_of_parts, parts_sleep, summary_sleep = graph_params
    print(
        f"Bulding graph D with {num_of_clicks} clicks, "
        f"with {num_of_parts} parts per click and one summary task per click, "
        f"{parts_sleep} seconds for each part, and "
        f"{summary_sleep} seconds for the summary")

    for click in range(int(num_of_clicks)):
        parts = [task_graph.create_task(
            f"part {click}:{p}", task_part, args=[parts_sleep], deps=[])
            for p in range(int(num_of_parts))]
        task_graph.create_task(
            f"summary {click}", task_summary, args=[summary_sleep], deps=parts)
    return task_graph


def _build_graph_b(graph_params: list[str] | None) -> TaskGraph:
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

    parts = [task_graph.create_task(
        f"part {p}", task_part_b, args=[parts_sleep], deps=[])
        for p in range(int(num_of_parts))]
    task_graph.create_task(
        "summary", task_summary, args=[summary_sleep], deps=parts)
    return task_graph


def _build_graph_c(graph_params: list[str] | None) -> TaskGraph:
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

    parts = [
        task_graph.create_task(
            f"part {p}", task_part_c, args=[parts_sleep], deps=[])
        for p in range(int(num_of_parts))
    ]
    summary = task_graph.create_task(
        "summary", task_summary, args=[summary_sleep], deps=parts)
    parts2 = [
        task_graph.create_task(
            f"part2 {p}", task_part, args=[summary], deps=[summary])
        for p in range(int(num_of_parts))
    ]
    task_graph.create_task("summary2", task_summary, args=[], deps=parts2)
    return task_graph


def build_demo_graph(graph_type: str,
                     graph_params: list[str] | None) -> TaskGraph:
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


def main(argv: list[str] | None = None) -> None:
    """Entry point for the demo script."""
    random.seed(42)

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
