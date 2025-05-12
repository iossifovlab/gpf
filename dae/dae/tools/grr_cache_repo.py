"""Provides CLI tools for caching genomic resources."""

import argparse
import logging
import os
import sys
import time

from dae.annotation.annotation_factory import load_pipeline_from_file
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.genomic_resources.cached_repository import cache_resources
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
    get_default_grr_definition,
    load_definition_file,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.utils.verbosity_configuration import VerbosityConfiguration

logger = logging.getLogger("grr_cache_repo")


def cli_cache_repo(argv: list[str] | None = None) -> None:
    """CLI for caching genomic resources."""
    if not argv:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Genomic resources cache tool - caches genomic resources "
        "for a given repository")
    parser.add_argument(
        "--grr", "-g", default=None, help="Repository definition file",
    )
    parser.add_argument(
        "--jobs", "-j", help="Number of jobs running in parallel",
        default=4, type=int,
    )
    parser.add_argument(
        "--instance", "-i", default=None,
        help="GPF instance configuration filegpf_instance.yaml to use",
    )
    parser.add_argument(
        "--annotation", "-a", default=None,
        help="Annotation configuration file annotation.yaml to use",
    )
    VerbosityConfiguration.set_arguments(parser)

    args = parser.parse_args(argv)
    VerbosityConfiguration.set(args)

    start = time.time()
    if args.grr is not None:
        definition = load_definition_file(args.grr)
    else:
        definition = get_default_grr_definition()

    grr = build_genomic_resource_repository(definition=definition)

    resources: set[str] = set()

    if args.instance is not None and args.annotation is not None:
        raise ValueError(
            "This tool cannot handle both annotation and instance parameters.",
        )

    annotation: AnnotationPipeline | None = None
    if args.instance is not None:
        instance_file = os.path.abspath(args.instance)
        gpf_instance = GPFInstance.build(instance_file, grr=grr)
        annotation = gpf_instance.get_annotation_pipeline()

    elif args.annotation is not None:
        annotation = load_pipeline_from_file(args.annotation, grr)

    if annotation is not None:
        for annotator in annotation.annotators:
            resources = resources | {
                resource.get_id() for resource in annotator.resources}

    cache_resources(grr, resource_ids=resources, workers=args.jobs)

    elapsed = time.time() - start
    logger.info("Cached all resources in %.2f secs", elapsed)
