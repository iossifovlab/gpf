from __future__ import annotations

import argparse
import logging
import sys
from typing import Optional

from jinja2 import Environment, PackageLoader
from markdown2 import markdown

from dae.annotation.context import CLIAnnotationContext
from dae.genomic_resources.genomic_context import get_genomic_context
from dae.utils.verbosity_configuration import VerbosityConfiguration

logger = logging.getLogger("annotate_doc")


def configure_argument_parser() -> argparse.ArgumentParser:
    """Construct and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Annotate columns",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("pipeline", default="context", nargs="?",
                        help="The pipeline definition file. By default, or if "
                        "the value is gpf_instance, the annotation pipeline "
                        "from the configured gpf instance will be used.")
    parser.add_argument("-o", "--output",
                        help="Filename of the output VCF result",
                        default=None)
    CLIAnnotationContext.add_context_arguments(parser)
    VerbosityConfiguration.set_arguments(parser)
    return parser


def cli(raw_args: Optional[list[str]] = None) -> None:
    """Run command line interface for annotate_vcf tool."""
    if not raw_args:
        raw_args = sys.argv[1:]

    parser = configure_argument_parser()
    args = parser.parse_args(raw_args)
    VerbosityConfiguration.set(args)
    CLIAnnotationContext.register(args)

    context = get_genomic_context()
    pipeline = CLIAnnotationContext.get_pipeline(context)

    annotation_info = pipeline.get_info()

    env = Environment(loader=PackageLoader("dae.annotation", "templates"),
                      autoescape=True)
    template = env.get_template("annotate_doc_pipeline_template.jinja")
    html_doc = template.render(annotation_pipeline_info=annotation_info,
                               markdown=markdown)
    if args.output:
        with open(args.output, "w") as outfile:
            outfile.write(html_doc)
    else:
        print(html_doc)


if __name__ == "__main__":
    cli(sys.argv[1:])
