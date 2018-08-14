#!/usr/bin/env python

from __future__ import unicode_literals
import argparse
import sys
import time
import datetime
from os.path import exists
import pandas as pd
import numpy as np
from future import standard_library
standard_library.install_aliases()
from configparser import ConfigParser
from builtins import object, str
from box import Box
import matplotlib.pyplot as plt

import common.config


def get_argument_parser():
    desc = """Program to generate histogram data by given score files"""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('--config', required=True, action='store',
                        help='config file location')
    parser.add_argument('infile', nargs='?', action='store', default='-',
                        help='comma separated list of paths for input files')
    parser.add_argument('outfile', nargs='?', action='store', default='-',
                        help='comma separated list of paths for outfile files;'
                             'default to score names')

    return parser


class GenerateScoresHistograms(object):

    def __init__(self, input_files, output_files, scores):
        self.genomic_score_files = input_files
        self.output_files = output_files
        self.scores = scores

    def generate_scores_histograms(self, xscales, yscales, bins_num, ranges):
        for output_file, score, xscale, yscale, bin_num in\
                zip(self.output_files, self.scores, xscales,
                    yscales, bins_num):
            values = pd.DataFrame(columns=[score])

            for genomic_score_file in self.genomic_score_files:
                v = pd.read_csv(genomic_score_file, usecols=[score], sep='\t', encoding='utf-8')
                v = pd.to_numeric(v[score], errors='coerce')
                v = pd.DataFrame(v)
                values = pd.concat([values, v])

            if score in ranges:
                range = ranges[score]
            else:
                range = [values.min().values[0], values.max().values[0]]

            if xscale == 'linear':
                bars, bins = np.histogram(values[score].values, bins=bin_num,
                                          range=range)
            elif xscale == 'log':
                bins = []
                if range[0] == 0:
                    bins = [0.0]
                    range[0] += 1
                    bin_num -= 1
                bins = bins + list(np.logspace(np.log10(range[0]),
                                               np.log10(range[1]), bin_num))

                bins = list(bins)
                bars, bins = np.histogram(values[score].values, bins)

            # print(bins, bars)
            scores = pd.Series(bins, name='scores')
            data = pd.Series(bars, name=score)
            histogram = pd.concat([data, scores], axis=1)
            histogram_csv = histogram.to_csv(index=False)

            output_file.write(str(histogram_csv))


            histogram.dropna(inplace=True)
            bins = histogram['scores'].values
            bars = list(map(int, histogram[score].values))
            fig, ax = plt.subplots()
            plt.yscale(yscale)
            ax.bar(bins, bars, width=0.01)
            plt.savefig(output_file + '.png')

            print('Generating {} finished'.format(score))


def main():
    start = time.time()

    opts = get_argument_parser().parse_args()

    config = ConfigParser()
    config.optionxform = str
    config.read(opts.config)
    config = Box(common.config.to_dict(config),
                 default_box=True, default_box_attr=None)

    scores = []
    xscale = []
    yscale = []
    bins_num = []
    ranges = {}
    output_files = []
    for score in config.genomicScores.scores.split(','):
        scores.append(score)
        output_files.append(config['genomicScores.{}'.format(score)].file)
        xscale.append(config['genomicScores.{}'.format(score)].xscale)
        yscale.append(config['genomicScores.{}'.format(score)].yscale)
        bins_num.append(int(config['genomicScores.{}'.format(score)].bins))
        if config['genomicScores.{}'.format(score)].range:
            ranges[score] =\
                list(map(float, config['genomicScores.{}'.format(
                    score)].range.split(',')))

    if opts.infile == '-':
        sys.stderr.write("You must provide input file!\n")
        sys.exit(-78)

    input_files = opts.infile.split(',')

    for input_file in input_files:
        if not exists(input_file):
            sys.stderr.write("The given input file does not exist!\n")
            sys.exit(-78)

    gsh = GenerateScoresHistograms(input_files, output_files, scores)
    gsh.generate_scores_histograms(xscale, yscale, bins_num, ranges)

    sys.stderr.write(
        "The program was running for [h:m:s]: " +
        str(datetime.timedelta(seconds=round(time.time() - start, 0))) + "\n")


if __name__ == '__main__':
    main()
