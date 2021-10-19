# import sys
# import time
# import argparse
# import logging
# import os
# import yaml
# from urllib.parse import urlparse
# from dataclasses import dataclass
# from concurrent.futures import ThreadPoolExecutor

# from dae.gpf_instance.gpf_instance import GPFInstance
# from dae.genomic_resources.repository import FSGenomicResourcesRepo
# from dae.genomic_resources.score_statistics import PositionScoreStatistic, \
#     Histogram

# logger = logging.getLogger(__name__)


# @dataclass
# class RegionStats:
#     histograms: dict
#     chrom: str
#     positions_covered_counts: dict
#     min_values: dict
#     max_values: dict


# def count_region(resource, chrom, start, end):

#     histograms = dict()
#     positions_covered_counts = dict()
#     min_values = dict()
#     max_values = dict()
#     for score in resource.get_all_scores():
#         histogram_config = \
#             resource.get_score_default_annotation(score)["histogram"]
#         histograms[score] = Histogram.from_config(histogram_config)
#         positions_covered_counts[score] = 0
#         min_values[score] = None
#         max_values[score] = None

#     for line in resource._fetch_lines(chrom, start, end):
#         for score in resource.get_all_scores():
#             histogram = histograms[score]
#             value = line.scores[score]
#             if histogram.add_value(value):
#                 min_value = min_values[score]
#                 if min_value is None or value < min_value:
#                     min_values[score] = value
#                 max_value = max_values[score]
#                 if max_value is None or value > max_value:
#                     max_values[score] = value
#                 positions_covered_counts[score] += 1

#     return RegionStats(
#         histograms, chrom,
#         positions_covered_counts,
#         min_values, max_values
#     )


# def main(argv, gpf_instance=None):
#     parser = argparse.ArgumentParser(
#         description="Score resource statistic generation tool",
#         conflict_handler="resolve",
#         formatter_class=argparse.RawDescriptionHelpFormatter,
#     )

#     parser.add_argument(
#         "resource_id",
#         type=str,
#         metavar="<resource id>",
#         help="ID of the resource to generate statistics"
#     )

#     parser.add_argument(
#         "--repository-path",
#         type=str,
#         metavar="<repo path>",
#         dest="repo_path",
#         default=None,
#         help="Path to genomic score repository"
#     )

#     parser.add_argument(
#         "--repository-id",
#         type=str,
#         metavar="<repo id>",
#         dest="repo_id",
#         default=None,
#         help="Genomic score repository ID in GPF instance"
#     )

#     parser.add_argument(
#         "-j", "--jobs",
#         type=int,
#         metavar="<jobs>",
#         dest="jobs",
#         default=4,
#         help="Amount of jobs to create for counting"
#     )

#     parser.add_argument(
#         "--region-length",
#         type=int,
#         metavar="<region length>",
#         dest="region_length",
#         default=500_000,
#         help="Chromosome region size"
#     )

#     parser.add_argument(
#         "--genome-file",
#         type=str,
#         metavar="<genome file>",
#         dest="genome_file",
#         default=None,
#         help=(
#             "Genome file to use, "
#             "will try to create GPFInstance if unspecified"
#         )
#     )

#     parser.add_argument(
#         "--output-dir",
#         type=str,
#         metavar="<output directory>",
#         dest="output_dir",
#         default=None,
#         help=(
#             "Where to store score yaml files. "
#             "Will automatically create a scores directory in resource "
#             "if not given"
#         )
#     )

#     args = parser.parse_args(argv)

#     resource = None

#     if args.repo_id is not None or args.genome_file is None:
#         if gpf_instance is None:
#             try:
#                 gpf_instance = GPFInstance()
#             except Exception as e:
#                 logger.warning("GPF not configured correctly")
#                 logger.exception(e)
#                 return

#     if args.repo_id is not None:
#         resource = gpf_instance.genomic_resource_db.get_resource(
#             args.resource_id, args.repo_id
#         )
#     elif args.repo_path is not None:
#         try:
#             repository = FSGenomicResourcesRepo(
#                 "temp", f"{args.repo_path}"
#             )
#             repository.load()
#             resource = repository.get_resource(args.resource_id)
#         except Exception as e:
#             logger.error(
#                 f"Failed to find resource f{args.resource_id} "
#                 f"in repository at f{args.repo_path}"
#             )
#             logger.exception(e)
#             return
#     else:
#         logger.error("Failed to acquire repository. Exiting...")
#         return

#     score_ids = resource.get_all_scores()

#     resource.open()

#     genome = gpf_instance.genomes_db.get_genome()
#     genomic_sequence = genome.get_genomic_sequence()
#     chromosome_lengths = {
#         chrom: genomic_sequence.get_chrom_length(chrom)
#         for chrom in resource.get_all_chromosomes()
#     }
#     print(chromosome_lengths)

#     score_statistics = dict()
#     for score in score_ids:
#         histogram_config = \
#             resource.get_score_default_annotation(score)["histogram"]
#         histogram = Histogram.from_config(histogram_config)
#         score_statistics[score] = PositionScoreStatistic(histogram)

#     executor = ThreadPoolExecutor(max_workers=args.jobs)

#     start = time.time()

#     futures = list()

#     for chrom, chrom_length in chromosome_lengths.items():
#         for start in range(1, chrom_length, args.region_length):
#             end = start + args.region_length - 1
#             future = executor.submit(
#                 count_region,
#                 resource, chrom, start, end
#             )
#             futures.append(future)

#     results = [f.result() for f in futures]

#     score_positions_covered = {score_id: dict() for score_id in score_ids}

#     for res in results:
#         for score in score_ids:
#             stat = score_statistics[score]
#             hist1 = stat.histogram
#             hist2 = res.histograms[score]
#             stat.histogram = Histogram.merge(
#                 hist1, hist2
#             )
#             min_value = res.min_values[score]
#             if (
#                 stat.min_value is None or
#                 min_value is not None and stat.min_value < min_value
#             ):
#                 stat.min_value = min_value
#             max_value = res.max_values[score]
#             if (
#                 stat.max_value is None or
#                 max_value is not None and stat.max_value < max_value
#             ):
#                 stat.max_value = max_value

#             if res.chrom not in score_positions_covered[score]:
#                 score_positions_covered[score][res.chrom] = 0

#             score_positions_covered[score][res.chrom] += \
#                 res.positions_covered_counts[score]

#     for score in score_ids:
#         stat = score_statistics[score]
#         covered_all_prc_sum = 0
#         missing = 0
#         for chrom, length in chromosome_lengths.items():
#             covered_count = score_positions_covered[score][chrom]
#             covered_prc = (covered_count / length) * 100
#             stat.positions_covered[chrom] = covered_prc

#             covered_all_prc_sum += covered_prc

#             missing += length - covered_count

#         covered_all_prc_sum /= len(chromosome_lengths)
#         stat.missing_count = missing
#         stat.positions_covered_all = covered_all_prc_sum

#     end = time.time()
#     elapsed = end - start
#     print(elapsed)

#     output_dir = args.output_dir
#     if output_dir is None:
#         output_dir_url = os.path.join(resource.get_url(), "scores")
#         output_dir = urlparse(output_dir_url).path
#     os.makedirs(output_dir, exist_ok=True)
#     for score in score_ids:
#         with open(os.path.join(output_dir, f"{score}.yaml"), "w") as file:
#             stat = score_statistics[score]
#             yaml.dump(stat.to_dict(), file, default_flow_style=False)


# if __name__ == "__main__":
#     main(sys.argv[1:])
