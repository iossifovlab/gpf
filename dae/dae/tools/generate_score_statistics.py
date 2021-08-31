import sys
import time
import argparse
import logging

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.genomic_resources.repository import FSGenomicResourcesRepo
from dae.genomic_resources.score_statistics import PositionScoreStatistic, \
    Histogram

logger = logging.getLogger(__name__)


def count_chrom(resource, statistic, score_id, chrom, chrom_length):
    chunk_size = 500_000

    for start in range(1, chrom_length, chunk_size):
        end = start + chunk_size - 1
        for line in resource._fetch_lines(chrom, start, end):
            value = line[score_id]
            if statistic.min_value is None or value < statistic.min_value:
                statistic.min_value = value
            if statistic.max_value is None or value > statistic.max_value:
                statistic.max_value = value
            statistic.positions_covered[line["position"]] = True
            statistic.histogram.add_value(value)


def main(argv, gpf_instance=None):
    parser = argparse.ArgumentParser(
        description="Score resource statistic generation tool",
        conflict_handler="resolve",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "resource-id",
        type=str,
        metavar="<resource id>",
        dest="resource_id",
        help="ID of the resource to generate statistics"
    )

    parser.add_argument(
        "--repository-path",
        type=str,
        metavar="<repo path>",
        dest="repo_path",
        default=None,
        help="Path to genomic score repository"
    )

    parser.add_argument(
        "--repository-id",
        type=str,
        metavar="<repo id>",
        dest="repo_id",
        default=None,
        help="Genomic score repository ID in GPF instance"
    )

    args = parser.parse_args(argv)

    resource = None

    if args.repo_id is not None:
        if gpf_instance is None:
            try:
                gpf_instance = GPFInstance()
                resource = gpf_instance.genomic_resource_db.get_resource(
                    args.resource_id, args.repo_id
                )
            except Exception as e:
                logger.warning("GPF not configured correctly")
                logger.exception(e)
    elif args.repo_path is not None:
        try:
            repository = FSGenomicResourcesRepo(
                "temp", f"file://{args.repo_path}"
            )
            repository.load()
            resource = repository.get_resource(args.resource_id)
        except Exception as e:
            logger.error(
                f"Failed to find resource f{args.resource_id} "
                f"in repository at f{args.repo_path}"
            )
            logger.exception(e)
    else:
        logger.error("Failed to acquire repository. Exiting...")
        return

    score_ids = resource.get_all_scores()

    genome = gpf_instance.genomes_db.get_genome()
    genomic_sequence = genome.get_genomic_sequence()
    chromosome_lengths = {
        chrom: genomic_sequence.get_chrom_length(chrom)
        for chrom in resource.get_all_chromosomes()
    }

    score_statistics = dict()
    for score in score_ids:
        histogram_config = \
            resource.get_score_default_annotation(score)["histogram"]
        histogram = Histogram.from_config(histogram_config)
        score_statistics[score] = PositionScoreStatistic(histogram)

    start = time.time()

    for score in score_ids:
        for chrom, chrom_length in chromosome_lengths.items():
            count_chrom(
                resource, score_statistics[score], score, chrom, chrom_length
            )

    end = time.time()
    elapsed = end - start
    print(elapsed)


if __name__ == "__main__":
    main(sys.argv[1:])
