#!/usr/bin/env python
import argparse
import logging
from typing import Optional

from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.gpf_instance.gpf_instance import GPFInstance


def main(
    gpf_instance: Optional[GPFInstance] = None,
    argv: Optional[list[str]] = None
) -> None:
    """Generate denovo gene sets CLI."""
    description = "Generate genovo gene sets tool"
    parser = argparse.ArgumentParser(description=description)
    VerbosityConfiguration.set_arguments(parser)

    parser.add_argument(
        "--show-studies",
        help="This option will print available "
        "genotype studies and groups names",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--studies",
        help="Specify genotype studies and groups "
        "names for generating denovo gene sets. Default to all.",
        default=None,
        action="store",
    )

    args = parser.parse_args(argv)

    VerbosityConfiguration.set(args)
    logging.getLogger("impala").setLevel(logging.WARNING)

    if gpf_instance is None:
        gpf_instance = GPFInstance.build()
    denovo_gene_sets_db = gpf_instance.denovo_gene_sets_db

    if args.show_studies:
        for study_id in denovo_gene_sets_db.get_genotype_data_ids():
            print(study_id)
    else:
        if args.studies:
            filter_studies_ids = None
            studies = args.studies.split(",")
        else:
            studies = gpf_instance.get_genotype_data_ids()

        print("generating de Novo gene sets for studies:", studies)
        filter_studies_ids = [
            study_id
            for study_id in denovo_gene_sets_db.get_genotype_data_ids()
            if study_id in studies
        ]
        # pylint: disable=protected-access
        denovo_gene_sets_db._build_cache(filter_studies_ids)


if __name__ == "__main__":
    main()
