#!/usr/bin/env python
import logging
import argparse

from dae.genomic_resources.repository import GenomicResourcesRepo

logger = logging.getLogger(__name__)


def main(argv=None):
    description = (
        "Tool for creating/updating the metadata required for a "
        "genomic resource repository to be created."
    )
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--verbose', '-V', '-v', action='count', default=0)

    args = parser.parse_args(argv)
    if args.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif args.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    GenomicResourcesRepo.create_genomic_resource_repository(".")

    logger.info("Done")


if __name__ == "__main__":
    main()
