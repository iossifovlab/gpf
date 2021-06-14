#! /usr/bin/env python

import os
import argparse
import logging
import math
import time

from concurrent.futures import ThreadPoolExecutor, as_completed

import yaml
import pysam

import numpy as np
import pandas as pd

from dae import GPFInstance

import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.use("PS")  # noqa
plt.ioff()  # noqa


logger = logging.getLogger(__name__)


def region_bins_count(chrom_length, region_length):
    return math.ceil(chrom_length / region_length)


def build_regions(chromosome_lengths, region_length):
    result = []
    for chrom, chrom_length in chromosome_lengths.items():
        bins_count = region_bins_count(chrom_length, region_length)
        if bins_count == 1:
            result.append(chrom)
            continue

        for region_index in range(bins_count):
            start = region_index * region_length + 1
            end = (region_index + 1) * region_length
            if end > chrom_length:
                end = chrom_length
            result.append(f"{chrom}:{start}-{end}")

    return result


class Range:
    def __init__(self, start=np.inf, end=-np.inf):
        self.min = start
        self.max = end

    def __repr__(self):
        return f"Range({self.min}-{self.max})"

    def isin(self, val):
        return self.min <= val <= self.max


def collect_range(vcf, region, scores):
    start = time.time()
    result = {s: Range() for s in scores}
    for count, v in enumerate(vcf(region)):
        for score in scores:
            val = v.info.get(score)
            if not val:
                continue
            val = float(val[0])
            score_range = result[score]
            if val > score_range.max:
                score_range.max = val
            if val < score_range.min:
                score_range.min = val
        if (count) % 100_000 == 0:
            elapsed = time.time() - start
            logger.debug(
                f"progress {region}: {count}; "
                f"{v.chrom}:{v.pos}; {elapsed:.2f} sec")
    return result


class ScoreHistogram:
    def __init__(self, xscale, bins_count, score_range):
        self.xscale = xscale
        self.bins_count = bins_count
        self.domain_range = score_range

        if xscale == "linear":
            self.bins = np.linspace(
                self.domain_range.min,
                self.domain_range.max,
                self.bins_count + 1)
            print(self.bins)
        elif xscale == "log":
            min_range = self.domain_range.min
            self.bins = []
            if self.domain_range.min <= 0:
                assert self.domain_range.min >= 0.0

                step = float(
                    self.domain_range.max - self.domain_range.min) / \
                    self.bins_count

                min_range = step / bins_count
                self.bins = [0.0]
                bins_count -= 1
            self.bins = self.bins + list(
                np.logspace(
                    np.log10(min_range), np.log10(self.domain_range.max),
                    bins_count + 1)
            )

        self.bins = np.array(self.bins)
        self.bars = np.zeros(len(self.bins))

    def update_histogram(self, val):
        if val is None:
            return
        assert self.domain_range.isin(val)

        print(np.abs(self.bins - val))
        index = (np.abs(self.bins - val)).argmin()
        print(index)
        self.bars[index] += 1

    def merge(self, hist):
        assert len(self.bins) == len(hist.bins)
        assert len(self.bars) == len(hist.bars)
        assert self.domain_range.min == hist.domain_range.min
        assert self.domain_range.max == hist.domain_range.max

        self.bars += hist.bars


def collect_histograms(vcf, region, scores):
    start = time.time()
    result = {s: ScoreHistogram("log", 100, sr) for s, sr in scores.items()}

    for count, v in enumerate(vcf(region)):
        for score, hist in result.items():
            val = v.info.get(score)
            if not val:
                continue
            val = float(val[0])
            hist.update_histogram(val)

        if (count) % 100_000 == 0:
            elapsed = time.time() - start
            logger.debug(
                f"progress {region}: {count}; "
                f"{v.CHROM}:{v.POS}; {elapsed:.2f} sec")
    return result


def store_domain_ranges(domain_ranges, output):
    out = {
        s: {"min": r.min, "max": r.max} for s, r in domain_ranges.items()
    }
    yaml.dump(out, output)


def load_domain_ranges(infile):
    res = yaml.load(infile, Loader=yaml.Loader)

    result = {}
    for s, r in res.items():
        result[s] = Range(r["min"], r["max"])
    return result


def build_scores_domains(scores_filename, scores, regions, threads=20):
    executor = ThreadPoolExecutor(threads)
    futures = []

    for count, region in enumerate(regions):
        logger.info(f"starting range processing for region {region}")

        vcf = pysam.VariantFile(scores_filename)
        future = executor.submit(collect_range, vcf, region, scores)
        futures.append(future)

    print("waiting for any job to complete...")
    result = {s: Range() for s in scores}
    for future in as_completed(futures):
        data = future.result()
        print(data)
        for score, score_range in data.items():
            result[score].min = min(result[score].min, score_range.min)
            result[score].max = max(result[score].max, score_range.max)

    return result


def build_histograms(scores_filename, scores, regions, threads=20):
    executor = ThreadPoolExecutor(threads)
    futures = []

    for count, region in enumerate(regions):
        logger.info(f"starting range processing for region {region}")

        vcf = pysam.VariantFile(scores_filename)
        future = executor.submit(collect_histograms, vcf, region, scores)
        futures.append(future)

    print("waiting for any job to complete...")
    result = {s: ScoreHistogram("log", 100, sr) for s, sr in scores.items()}
    for future in as_completed(futures):
        data = future.result()
        for score, hist in data.items():
            result[score].merge(hist)

    return result


def save_histogram(basename, hist):
    scores = pd.Series(hist.bins, name="scores")
    data = pd.Series(hist.bars, name=basename)
    histogram = pd.concat([data, scores], axis=1, sort=True)
    histogram.to_csv(f"{basename}.csv", index=False)

    histogram.dropna(inplace=True)
    bins = list(histogram["scores"].values)
    bars = list(map(int, histogram[basename].values))
    _, ax = plt.subplots()
    plt.yscale("log")
    plt.xscale(hist.xscale)

    ax.bar(bins, bars, width=0.01)
    plt.savefig(f"{basename}.png")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verbose", "-V", action='count', default=0)
    parser.add_argument(
        "--total", "-T", action="store", type=int, default=1000)
    parser.add_argument(
        "--batch", "-B", action="store", type=int, default=100)
    parser.add_argument(
        "--region", "-r", action="store", type=int, default=3_000_000_000)
    parser.add_argument(
        "--threads", "-p", action="store", type=int, default=20)

    parser.add_argument(
        "--build-domains", action="store_true", default=False)
    parser.add_argument(
        "--output", "-o", action="store", type=str)
    parser.add_argument(
        "--domain-ranges", action="store", type=str)

    parser.add_argument(
        "score_file", action="store", type=str, default=None)
    parser.add_argument(
        "scores", action="store", type=str, default=None)

    argv = parser.parse_args()
    assert argv.scores is not None
    assert argv.score_file is not None
    assert os.path.exists(argv.score_file)

    if argv.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif argv.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif argv.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    gpf_instance = GPFInstance()
    genomes_db = gpf_instance.genomes_db

    chromosome_lengths = dict(
        genomes_db.get_genomic_sequence().get_all_chrom_lengths()[:24])

    regions = build_regions(chromosome_lengths, argv.region)
    scores = [str(s).strip() for s in argv.scores.split(",")]

    if argv.build_domains:
        result = build_scores_domains(
            argv.score_file, scores, regions, argv.threads)
        with open(argv.output, "w") as output:
            yaml.dump(result, output, default_flow_style=False)
        return

    assert argv.domain_ranges is not None
    assert os.path.exists(argv.domain_ranges), argv.domain_ranges

    with open(argv.domain_ranges, "r") as infile:
        domain_ranges = load_domain_ranges(infile)
    assert domain_ranges is not None
    print(domain_ranges)

    result = build_histograms(
        argv.score_file, domain_ranges, regions, argv.threads)

    for name, hist in result.items():
        save_histogram(name, hist)


if __name__ == "__main__":
    main()
