#!/usr/bin/env python
import argparse
import logging

from dae.gpf_instance.gpf_instance import GPFInstance


def main(gpf_instance=None, argv=None):
    description = "Generate genovo gene sets tool"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--verbose', '-V', action='count', default=0)

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

    if args.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif args.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    if gpf_instance is None:
        gpf_instance = GPFInstance()
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
        denovo_gene_sets_db._build_cache(filter_studies_ids)


if __name__ == "__main__":
    main()
