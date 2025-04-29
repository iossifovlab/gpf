"""Provides CLI tools for caching genomic resources."""

import argparse
import logging
import os
import sys
import time

from dae.annotation.annotation_factory import (
    build_annotation_pipeline,
    load_pipeline_from_file,
)
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.dae_conf import dae_conf_schema
from dae.genomic_resources.cached_repository import cache_resources
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
    get_default_grr_definition,
    load_definition_file,
)
from dae.utils.verbosity_configuration import VerbosityConfiguration

logger = logging.getLogger("grr_cache_repo")


def cli_cache_repo(argv: list[str] | None = None) -> None:
    """CLI for caching genomic resources."""
    if not argv:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Genomic resources cache tool - caches genomic resources for a given repository")  # noqa: E501
    parser.add_argument(
        "--grr", "-g", default=None, help="Repository definition file",
    )
    parser.add_argument(
        "--jobs", "-j", help="Number of jobs running in parallel",
        default=4, type=int,
    )
    parser.add_argument(
        "--instance", "-i", default=None,
        help="gpf_instance.yaml to use for selective cache",
    )
    parser.add_argument(
        "--annotation", "-a", default=None,
        help="annotation.yaml to use for selective cache",
    )
    VerbosityConfiguration.set_arguments(parser)

    args = parser.parse_args(argv)
    VerbosityConfiguration.set(args)

    start = time.time()
    if args.grr is not None:
        definition = load_definition_file(args.grr)
    else:
        definition = get_default_grr_definition()

    repository = build_genomic_resource_repository(definition=definition)

    resources: set[str] = set()
    pipeline = None

    if args.instance is not None and args.annotation is not None:
        raise ValueError(
            "This tool cannot handle both annotation and instance flags",
        )

    if args.instance is not None:
        instance_file = os.path.abspath(args.instance)
        gpf_config = GPFConfigParser.load_config(
            instance_file, dae_conf_schema)
        genome_id = gpf_config.reference_genome.resource_id
        resources.add(genome_id)
        gene_models_id = gpf_config.gene_models.resource_id
        resources.add(gene_models_id)

        if gpf_config.annotation.conf_file is not None:
            pipeline = load_pipeline_from_file(
                gpf_config.annotation.conf_file, repository)
        elif gpf_config.annotation.config is not None:
            pipeline = build_annotation_pipeline(
                gpf_config.annotation.config, repository)
    elif args.annotation is not None:
        pipeline = load_pipeline_from_file(args.annotation, repository)

    if pipeline is not None:
        annotation_resources = extract_resource_ids_from_pipeline(pipeline)
        resources |= annotation_resources

    cache_resources(repository, resource_ids=resources, workers=args.jobs)

    elapsed = time.time() - start
    logger.info("Cached all resources in %.2f secs", elapsed)


def extract_resource_ids_from_pipeline(
    pipeline: AnnotationPipeline,
) -> set[str]:
    """Collect resources and resource files used by annotation."""
    resources: set[str] = set()
    for annotator in pipeline.annotators:
        resources.update(resource.get_id() for resource in annotator.resources)
    return resources
