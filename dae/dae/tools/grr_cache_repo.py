"""Provides CLI tools for caching genomic resources."""

import sys
import os
import argparse
import time
import logging

from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.genomic_resources.repository_factory import load_definition_file, \
    get_default_grr_definition, \
    build_genomic_resource_repository
from dae.genomic_resources.cached_repository import \
    GenomicResourceCachedRepo, cache_resources
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.dae_conf import dae_conf_schema
from dae.annotation.annotation_factory import AnnotationConfigParser, \
    build_annotation_pipeline


logger = logging.getLogger("grr_cache_repo")


def cli_cache_repo(argv=None):
    """CLI for caching genomic resources."""
    if not argv:
        argv = sys.argv[1:]

    description = "Genomic resources cache tool - caches genomic resources " \
        "for a given repository"

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--grr", "-g", default=None, help="Repository definition file"
    )
    parser.add_argument(
        "--jobs", "-j", help="Number of jobs running in parallel",
        default=4, type=int,
    )
    parser.add_argument(
        "--instance", "-i", default=None,
        help="gpf_instance.yaml to use for selective cache"
    )
    parser.add_argument(
        "--annotation", "-a", default=None,
        help="annotation.yaml to use for selective cache"
    )
    VerbosityConfiguration.set_argumnets(parser)

    args = parser.parse_args(argv)
    VerbosityConfiguration.set(args)

    start = time.time()
    if args.grr is not None:
        definition = load_definition_file(args.grr)
    else:
        definition = get_default_grr_definition()

    repository = build_genomic_resource_repository(definition=definition)
    if not isinstance(repository, GenomicResourceCachedRepo):
        raise ValueError(
            "This tool works only if the top configured "
            "repository is cached.")

    resources: set[str] = set()
    annotation = None

    if args.instance is not None and args.annotation is not None:
        raise ValueError(
            "This tool cannot handle both annotation and instance flags"
        )

    if args.instance is not None:
        instance_file = os.path.abspath(args.instance)
        gpf_config = GPFConfigParser.load_config(
            instance_file, dae_conf_schema)
        genome_id = gpf_config.reference_genome.resource_id
        resources.add(genome_id)
        gene_models_id = gpf_config.gene_models.resource_id
        resources.add(gene_models_id)

        if gpf_config.annotation is not None:
            annotation = gpf_config.annotation.conf_file
    elif args.annotation is not None:
        annotation = args.annotation

    if annotation is not None:
        config = AnnotationConfigParser.parse_config_file(annotation)
        annotation_resources = extract_resource_ids_from_annotation(
            config, repository
        )
        resources |= annotation_resources

    cache_resources(repository, resource_ids=resources, workers=args.jobs)

    elapsed = time.time() - start
    logger.info("Cached all resources in %.2f secs", elapsed)


def extract_resource_ids_from_annotation(config, repository) -> set[str]:
    """Collect resources and resource files used by annotation."""
    resources: set[str] = set()
    with build_annotation_pipeline(
            pipeline_config=config, grr_repository=repository) as pipeline:
        for annotator in pipeline.annotators:
            resources = resources | annotator.resources
    return resources
