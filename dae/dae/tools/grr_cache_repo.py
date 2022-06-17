"""Provides CLI tools for caching genomic resources."""

import sys
import argparse
import time
import logging

from typing import cast

from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.genomic_resources.repository_factory import load_definition_file, \
    get_configured_definition, \
    build_genomic_resource_repository
from dae.genomic_resources.cached_repository import GenomicResourceCachedRepo
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.dae_conf import dae_conf_schema
from dae.annotation.annotation_factory import AnnotationConfigParser


logger = logging.getLogger("grr_cache_tool")


def cli_cache_repo(argv=None):
    """CLI for caching genomic resources."""
    if not argv:
        argv = sys.argv[1:]

    description = "Genomic resources cache tool - caches genomic resources " \
        "for a given repository"

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--definition", default=None, help="Repository definition file"
    )
    parser.add_argument(
        "--jobs", "-j", help="Number of jobs running in parallel",
        default=4, type=int,
    )
    parser.add_argument(
        "--instance", default=None,
        help="gpf_instance.yaml to use for selective cache"
    )
    parser.add_argument(
        "--annotation", default=None,
        help="annotation.yaml to use for selective cache"
    )
    VerbosityConfiguration.set_argumnets(parser)

    args = parser.parse_args(argv)
    VerbosityConfiguration.set(args)

    start = time.time()
    if args.definition is not None:
        definition = load_definition_file(args.definition)
    else:
        definition = get_configured_definition()

    repository = build_genomic_resource_repository(definition=definition)
    if not isinstance(repository, GenomicResourceCachedRepo):
        raise ValueError(
            "This tool works only if the top configured "
            "repository is cached.")
    repository = cast(GenomicResourceCachedRepo, repository)

    resources = set()
    annotation = None

    if args.instance is not None and args.annotation is not None:
        raise ValueError(
            "This tool cannot handle both annotation and instance flags"
        )

    if args.instance is not None:
        config = GPFConfigParser.load_config(args.instance, dae_conf_schema)
        resources.add(config.reference_genome.resource_id)
        resources.add(config.gene_models.resource_id)
        if config.annotation is not None:
            annotation = config.annotation.conf_file
    elif args.annotation is not None:
        annotation = args.annotation

    if annotation is not None:
        config = AnnotationConfigParser.parse_config_file(annotation)
        resources.update(_extract_resource_ids_from_annotation_conf(config))

    if len(resources) > 0:
        resources = list(resources)
    else:
        resources = None

    repository.cache_resources(workers=args.jobs, resource_ids=resources)

    elapsed = time.time() - start

    logger.info("Cached all resources in %.2f secs", elapsed)


def _extract_resource_ids_from_annotation_conf(config):
    resources = set()
    for annotator in config:
        print(annotator)
        for key, val in annotator.items():
            if key in [
                "resource_id",
                "target_genome",
                "chain",
                "genome"
            ]:
                resources.add(val)
    return resources
