#!/usr/bin/env python
import logging
import argparse
import sys

import numpy as np
import pandas as pd

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.score_file_conf import \
    score_file_conf_schema

from dae.configuration.schemas.genomic_scores import \
    genomic_score_schema

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.annotation.tools.score_file_io import ScoreFile

import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.use("PS")  # noqa
plt.ioff()  # noqa


logger = logging.getLogger("generate_histogram2.py")


def build_argument_parser():
    desc = """Program to generate histogram data by given score files"""
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('--verbose', '-V', action='count', default=0)

    parser.add_argument(
        "--histogram-config", required=True, action="store",
        help="histogram config file location"
    )

    parser.add_argument(
        "--score-file", required=True, action="store",
        help="score file location"
    )

    parser.add_argument(
        "--score-field", required=True, action="store",
        help="score field name to use for building the histogram",
    )

    parser.add_argument(
        "--range-min", required=False, action="store",
        type=float,
        help="score values range min",
    )

    parser.add_argument(
        "--range-max", required=False, action="store",
        type=float,
        help="score values range max",
    )

    parser.add_argument(
        "--range-log-min", required=False, action="store",
        type=float,
        help="score values log-range min",
    )

    parser.add_argument(
        "--score-name", required=True, action="store",
        help="output score name",
    )

    return parser


class Histogram:

    def __init__(self, bins_count, x_scale, x_min, x_max, x_log_min=None):
        self.bins_count = bins_count
        self.x_scale = x_scale
        self.x_min = x_min
        self.x_max = x_max

        if self.x_scale == "log":
            if x_log_min is not None:
                assert x_log_min > self.x_min
                self.x_log_min = x_log_min
            else:
                assert self.x_min == 0.0
                self.x_log_min = 0.01

        if self.x_scale == "linear":
            self.bins = np.linspace(
                self.x_min,
                self.x_max,
                self.bins_count,
            )
        elif self.x_scale == "log":
            self.bins = np.array([
                self.x_min,
                * np.logspace(
                    np.log10(self.x_log_min),
                    np.log10(self.x_max),
                    self.bins_count - 1
                )])
        else:
            assert False, f"unexpected xscale: {self.x_scale}"

        assert len(self.bins) == self.bins_count
        logger.info(f"bins: {self.bins}")

        self.bars = np.zeros(self.bins_count - 1, dtype=np.int32)

    def add_value(self, value):
        if value < self.x_min or value > self.x_max:
            logger.error(
                f"value {value} out of range: [{self.x_min},{self.x_max}]")
            return
        index = np.where(self.bins > value)
        if len(index) == 0:
            logger.error(f"(1) empty index {index} for value {value}")
            return
        index = index[0]
        if len(index) == 0:
            logger.info(f"(2) empty index {index} for value {value}")
            self.bars[-1] += 1
            return

        if index[0] == 0:
            logger.warning(
                f"value: {value}; with index {index} in bins: {self.bins}")

        self.bars[index[0] - 1] += 1

    @staticmethod
    def merge(hist1, hist2):
        assert hist1.bins_count == hist2.bins_count
        assert hist1.x_scale == hist2.x_scale
        assert hist1.x_min == hist2.x_min
        assert hist1.x_min_log == hist2.x_min_log
        assert hist1.x_max == hist2.x_max
        assert hist1.bins == hist2.bins

        result = Histogram(
            bins_count=hist1.bins_count,
            x_scale=hist1.x_scale,
            x_min=hist1.x_min,
            x_max=hist1.x_max,
            x_log_min=hist1.x_log_min)

        result.bars += hist1.bars
        result.bars += hist2.bars

        return result

    def save(self, score_name):
        scores = pd.Series(self.bins, name="scores")
        data = pd.Series(self.bars, name=score_name)
        histogram = pd.concat([data, scores], axis=1, sort=True)
        histogram.to_csv(score_name, index=False)


def main(argv):
    parser = build_argument_parser()
    argv = parser.parse_args(argv)

    if argv.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif argv.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif argv.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    histogram_config = GPFConfigParser.load_config(
        argv.histogram_config, genomic_score_schema
    )

    print(histogram_config)

    score_config = GPFConfigParser.load_config(
        f"{argv.score_file}.conf", score_file_conf_schema)
    print(score_config)

    assert argv.score_field in score_config.columns.score, (
        argv.score_field, score_config.score)

    gpf_instance = GPFInstance()

    genome = gpf_instance.genomes_db.get_genome()
    chromosome_lengths = dict(
        genome.get_genomic_sequence().get_all_chrom_lengths()
    )

    score = ScoreFile(argv.score_file)
    assert score is not None

    histogram = Histogram(
        bins_count=histogram_config.bins,
        x_scale=histogram_config.xscale,
        x_min=argv.range_min,
        x_max=argv.range_max,
        x_log_min=argv.range_log_min
    )
    assert histogram is not None

    chunk_size = 500_000
    for chrom, chrom_length in chromosome_lengths.items():

        for start in range(1, chrom_length, chunk_size):
            print(chrom, start, start+chunk_size - 1)
            for line in score.fetch_scores_iterator(
                    chrom, start, start + chunk_size - 1):
                value = line[argv.score_field]
                if value == '':
                    continue
                histogram.add_value(float(value))

    histogram.save(argv.score_name)  # "genome_gnomad_v3_af_percent"


if __name__ == "__main__":

    main(sys.argv[1:])
