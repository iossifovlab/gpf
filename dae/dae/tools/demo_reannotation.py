import sys
import argparse
from typing import Optional

from dae.annotation.context import CLIAnnotationContext
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.annotation_pipeline import ReannotationPipeline
from dae.genomic_resources.genomic_context import get_genomic_context


def configure_argument_parser() -> argparse.ArgumentParser:
    """Configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Annotate columns",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("pipeline_old", default="context", nargs="?")
    parser.add_argument("pipeline_new", default="context", nargs="?")
    CLIAnnotationContext.add_context_arguments(parser)
    return parser


def cli_graphical(raw_args: Optional[list[str]] = None) -> None:
    import graphviz

    if raw_args is None:
        raw_args = sys.argv[1:]

    parser = configure_argument_parser()
    args = parser.parse_args(raw_args)
    CLIAnnotationContext.register(args)
    context = get_genomic_context()
    grr = context.get_genomic_resources_repository()

    pipeline_new = build_annotation_pipeline(
        pipeline_config_file=args.pipeline_new,
        grr_repository=grr
    )
    pipeline_old = build_annotation_pipeline(
        pipeline_config_file=args.pipeline_old,
        grr_repository=grr
    )
    reannotation = ReannotationPipeline(pipeline_new, pipeline_old)
    dot = graphviz.Digraph(
        "reannotation", comment="Reannotation dependency graph"
    )
    dot.attr("node", shape="box", style="filled")

    annotator_ids = {}
    for idx, (annotator, _) in enumerate(
        reannotation.dependency_graph.items()
    ):
        annotator_ids[annotator] = f"A{idx}"

    def annotator_desc(annotator):
        resources = ", ".join(
            map(lambda r: r.resource_id, annotator.resources)
        )
        attrs = ", ".join(
            map(lambda a: f"{a.source} -> {a.name}", annotator.attributes)
        )
        desc = f"type: {annotator.type}\n  resources: {resources}\n  attrs: {attrs}"
        return "- " + desc

    for annotator, dependencies in reannotation.dependency_graph.items():
        annotator_id = annotator_ids[annotator]
        desc = annotator_desc(annotator)

        if annotator in reannotation.annotators_new:
            dot.attr("node", fillcolor="lightgreen")
        elif annotator in reannotation.upstream:
            dot.attr("node", fillcolor="lightblue")
        else:
            dot.attr("node", fillcolor="white")

        dot.node(annotator_id, desc)
        for dep, _ in dependencies:
            dep_id = annotator_ids[dep]
            dot.edge(dep_id, annotator_id)

    with dot.subgraph(name="cluster_1") as subgraph:
        subgraph.attr("node", fillcolor="indianred")
        subgraph.attr(label="deleted annotators")
        for idx, annotator in enumerate(reannotation.annotators_old):
            desc = annotator_desc(annotator)
            subgraph.node(f"OLDA{idx}", desc)

    dot.render(directory="graphviz-output")


def cli(raw_args: Optional[list[str]] = None) -> None:
    if raw_args is None:
        raw_args = sys.argv[1:]

    parser = configure_argument_parser()
    args = parser.parse_args(raw_args)
    CLIAnnotationContext.register(args)
    context = get_genomic_context()
    grr = context.get_genomic_resources_repository()

    pipeline_new = build_annotation_pipeline(
        pipeline_config_file=args.pipeline_new,
        grr_repository=grr
    )
    pipeline_old = build_annotation_pipeline(
        pipeline_config_file=args.pipeline_old,
        grr_repository=grr
    )
    reannotation = ReannotationPipeline(pipeline_new, pipeline_old)

    def annotator_desc(annotator):
        resources = ", ".join(
            map(lambda r: r.resource_id, annotator.resources)
        )
        attrs = ", ".join(
            map(lambda a: f"{a.source} -> {a.name}", annotator.attributes)
        )
        desc = f"type: {annotator.type}\n  resources: {resources}\n  attrs: {attrs}"
        return "- " + desc

    print("# NEW ANNOTATORS:")
    for annotator in reannotation.annotators_new:
        print(annotator_desc(annotator))
    print("# OLD ANNOTATORS:")
    for annotator in reannotation.annotators_old:
        print(annotator_desc(annotator))
    print("# MUST-BE-RERUN ANNOTATORS:")
    for annotator in reannotation.upstream + reannotation.downstream:
        print(annotator_desc(annotator))
    print("# UNCHANGED ANNOTATORS:")
    for annotator in reannotation.annotators_unchanged:
        print(annotator_desc(annotator))


if __name__ == "__main__":
    cli_graphical(sys.argv[1:])
