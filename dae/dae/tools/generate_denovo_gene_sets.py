import argparse
import logging
import sys

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.utils.verbosity_configuration import VerbosityConfiguration

logger = logging.getLogger("generate_denovo_gene_sets")


def main(
    argv: list[str] | None = None, *,
    gpf_instance: GPFInstance | None = None,
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
    parser.add_argument(
        "--force",
        help="Force generation of denovo gene sets even if they are already "
        "cached.",
        default=False,
        action="store_true",
    )
    if argv is None:
        argv = sys.argv[1:]

    args = parser.parse_args(argv)

    VerbosityConfiguration.set(args)

    if gpf_instance is None:
        gpf_instance = GPFInstance.build()
    denovo_gene_sets_db = gpf_instance.denovo_gene_sets_db

    study_ids = [
        study_id for study_id in denovo_gene_sets_db.get_genotype_data_ids()
        if not gpf_instance.get_genotype_data(study_id).is_remote
    ]

    if args.show_studies:
        for study_id in study_ids:
            logger.warning("study with denovo gene sets: %s", study_id)
    else:
        if args.studies:
            filtered_study_ids = None
            studies = args.studies.split(",")
        else:
            studies = gpf_instance.get_genotype_data_ids()

        filtered_study_ids = [
            study_id
            for study_id in study_ids
            if study_id in studies
        ]
        logger.info(
            "generating de Novo gene sets for studies: %s",
            filtered_study_ids)
        # pylint: disable=protected-access
        denovo_gene_sets_db.build_cache(
            filtered_study_ids, force=args.force)
