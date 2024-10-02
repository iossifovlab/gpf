from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from jinja2 import Environment, PackageLoader
from markdown2 import markdown

from dae.annotation.context import CLIAnnotationContext
from dae.genomic_resources.genomic_context import get_genomic_context
from dae.genomic_resources.genomic_scores import GenomicScore
from dae.genomic_resources.repository import GenomicResource
from dae.utils.verbosity_configuration import VerbosityConfiguration

logger = logging.getLogger("annotate_doc")


def configure_argument_parser() -> argparse.ArgumentParser:
    """Construct and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Annotate columns",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-o", "--output",
                        help="Filename of the output VCF result",
                        default=None)
    CLIAnnotationContext.add_context_arguments(parser)
    VerbosityConfiguration.set_arguments(parser)
    return parser


def cli(raw_args: list[str] | None = None) -> None:
    """Run command line interface for annotate_vcf tool."""
    if not raw_args:
        raw_args = sys.argv[1:]

    parser = configure_argument_parser()
    args = parser.parse_args(raw_args)
    VerbosityConfiguration.set(args)
    CLIAnnotationContext.register(args)

    context = get_genomic_context()
    pipeline = CLIAnnotationContext.get_pipeline(context)

    pipeline_path = None
    if os.path.exists(args.pipeline):
        pipeline_path = args.pipeline

    def make_resource_url(resource: GenomicResource) -> str:
        return resource.get_url()

    def make_histogram_url(score: GenomicScore, score_id: str) -> str | None:
        return score.get_histogram_image_url(score_id)

    env = Environment(loader=PackageLoader("dae.annotation", "templates"))  # noqa: S701
    template = env.get_template("annotate_doc_pipeline_template.jinja")
    html_doc = template.render(pipeline=pipeline,
                               pipeline_path=pipeline_path,
                               markdown=markdown,
                               res_url=make_resource_url,
                               hist_url=make_histogram_url)
    if args.output:
        Path(args.output).write_text(html_doc)
    else:
        print(html_doc)


if __name__ == "__main__":
    cli(sys.argv[1:])
