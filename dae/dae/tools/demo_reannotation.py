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

    def annotator_desc(annotator) -> str:
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
    for annotator in reannotation.annotators_removed:
        print(annotator_desc(annotator))
    print("# MUST-BE-RERUN ANNOTATORS:")
    for annotator in reannotation.annotators_changed:
        print(annotator_desc(annotator))
    print("# UNCHANGED ANNOTATORS:")
    for annotator in reannotation.annotators_unchanged:
        print(annotator_desc(annotator))


if __name__ == "__main__":
    cli(sys.argv[1:])
