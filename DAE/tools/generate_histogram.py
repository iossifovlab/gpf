#!/usr/bin/env python

from __future__ import unicode_literals

from future import standard_library
standard_library.install_aliases()  # noqa

import argparse
import sys
import time
import datetime
from os.path import exists
import pandas as pd
import numpy as np

from configparser import ConfigParser
from builtins import object, str
from box import Box
import matplotlib as mpl; mpl.use('PS')  # noqa
import matplotlib.pyplot as plt; plt.ioff()  # noqa

import common.config


def get_argument_parser():
    desc = """Program to generate histogram data by given score files"""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('--config', required=True, action='store',
                        help='config file location')
    parser.add_argument('--scores', required=False, action='store',
                        help='comma separated list of scores')
    parser.add_argument('-s', required=False, action='store',
                        help='start column')
    parser.add_argument('-e', required=False, action='store',
                        help='end column')
    parser.add_argument('-r', required=False, action='store',
                        help='Number of decimal places to round min and max')
    parser.add_argument('--chunk-size', required=False, action='store',
                        help='size of chunks to process')
    parser.add_argument('infile', nargs='?', action='store', default='-',
                        help='comma separated list of paths for input files')
    parser.add_argument('outfile', nargs='?', action='store', default='-',
                        help='comma separated list of paths for outfile files;'
                             'default to score names')

    return parser


class GenerateScoresHistograms(object):

    def __init__(self, input_files, output_files, scores, xscales, yscales,
                 bins_num, ranges, round_pos=None, chunk_size=None):
        self.genomic_score_files = input_files
        self.output_files = output_files
        self.scores = scores
        self.xscales = xscales
        self.yscales = yscales
        self.ranges = ranges
        self.bins_num = bins_num
        self.round_pos = round_pos
        self.chunk_size = chunk_size

    def get_min_max(self, file, head, score_column):
        min_value = None
        max_value = None

        for chunk in pd.read_csv(
            file, usecols=[score_column], sep='\t', header=head,
                chunksize=self.chunk_size, low_memory=True):
            chunk[score_column] = pd.to_numeric(
                chunk[score_column], errors='coerce')
            min_chunk = chunk[score_column].min()
            max_chunk = chunk[score_column].max()
            if min_value is None or min_chunk < min_value:
                min_value = min_chunk
            if max_value is None or max_chunk > max_value:
                max_value = max_chunk

        if self.round_pos is not None:
            min_value = np.around(min_value, self.round_pos)
            max_value = np.around(max_value, self.round_pos)

        return min_value, max_value

    def get_length(self, data, start, end):
        if start is not None and end is not None:
            data[start] = pd.to_numeric(data[start], errors='coerce')
            data[end] = pd.to_numeric(data[end], errors='coerce')
            data['length'] = data[end] - data[start]
            data['length'] += 1
            data = data.drop(columns=[start, end], axis=1)

        return data

    def get_bars_and_bins(self, xscale, range, bin_num):
        if xscale == 'linear':
            bins = np.linspace(range[0], range[1], bin_num)
        elif xscale == 'log':
            bins = []
            min_range = range[0]
            if range[0] == 0.0:
                bins = [0.0]
                min_range += 1
                bin_num -= 1
            bins = bins + list(np.logspace(np.log10(min_range),
                                           np.log10(range[1]),
                                           bin_num))
        bars = np.zeros(len(bins) - 1)
        bins = np.array(bins)

        return bars, bins

    def save_histogram(self, bars, bins, score, yscale, output_file):
        scores = pd.Series(bins, name='scores')
        data = pd.Series(bars, name=score)
        histogram = pd.concat([data, scores], axis=1)
        histogram.to_csv(output_file, index=False)

        histogram.dropna(inplace=True)
        bins = histogram['scores'].values
        bars = map(int, histogram[score].values)
        fig, ax = plt.subplots()
        plt.yscale(yscale)
        ax.bar(bins, bars, width=0.01)
        plt.savefig(output_file + '.png')

    def generate_scores_histograms(
            self, score_columns=None, start=None, end=None):
        if score_columns is None:
            score_columns = self.scores

        for output_file, score, xscale, yscale, bin_num, score_column in\
                zip(self.output_files, self.scores, self.xscales,
                    self.yscales, self.bins_num, score_columns):
            values = pd.DataFrame(columns=[score])

            for genomic_score_file in self.genomic_score_files:
                use_columns = [score_column]
                if start is not None and end is not None:
                    use_columns.extend([start, end])

                head = 'infer'
                if type(score_column) is int:
                    head = None

                if self.chunk_size is not None:
                    if score in self.ranges:
                        range = self.ranges[score]
                    else:
                        min_value, max_value = self.get_min_max(
                            genomic_score_file, head, score_column)
                        range = [min_value, max_value]

                    bars, bins = self.get_bars_and_bins(xscale, range, bin_num)
                    for chunk in pd.read_csv(
                        genomic_score_file, usecols=use_columns, sep='\t',
                            header=head, chunksize=self.chunk_size,
                            low_memory=True):
                        chunk = self.get_length(chunk, start, end)
                        chunk[score_column] = pd.to_numeric(
                            chunk[score_column], errors='coerce')
                        if 'length' in chunk:
                            for s, l in\
                                    zip(chunk[score_column], chunk['length']):
                                if s < range[0] or s > range[1]:
                                    continue
                                idx = (np.abs(bins - s)).argmin()
                                if idx == bin_num - 1:
                                    idx -= 1
                                bars[idx] += l
                        else:
                            for s in chunk[score_column]:
                                if s < range[0] or s > range[1]:
                                    continue
                                idx = (np.abs(bins - s)).argmin()
                                if idx == bin_num - 1:
                                    idx -= 1
                                bars[idx] += 1
                else:
                    v = pd.read_csv(genomic_score_file, usecols=use_columns,
                                    sep='\t', header=head)
                    v = self.get_length(v, start, end)
                    v = v.rename({score_column: score}, axis='columns')
                    v[score] = pd.to_numeric(v[score], errors='coerce')
                    v = pd.DataFrame(v)
                    values = pd.concat([values, v])

            if self.chunk_size is None:
                if score in self.ranges:
                    range = self.ranges[score]
                else:
                    if self.round_pos is None:
                        min_value = values[score].min()
                        max_value = values[score].max()
                    else:
                        min_value = np.around(values[score].min(),
                                              self.round_pos)
                        max_value = np.around(values[score].max(),
                                              self.round_pos)
                    range = [min_value, max_value]

                bars, bins = self.get_bars_and_bins(xscale, range, bin_num)

                if start is not None and end is not None:
                    for s, l in zip(values[score], values['length']):
                        if s < range[0] or s > range[1]:
                            continue
                        idx = (np.abs(bins - s)).argmin()
                        if idx == bin_num - 1:
                            idx -= 1
                        bars[idx] += l
                else:
                    bars = None

            if bars is None:
                bars, bins = np.histogram(
                    values[score].values, bins=bins, range=range)

            self.save_histogram(bars, bins, score, yscale, output_file)

            print('Generating {} finished'.format(score))


def main():
    start_time = time.time()

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

    score_columns = opts.scores
    if score_columns is not None:
        score_columns = [int(el) if el.isdigit() else el
                         for el in score_columns.split(',')]

    start = opts.s
    end = opts.e
    if start is not None and end is not None:
        if start.isdigit():
            start = int(opts.s)
        if end.isdigit():
            end = int(opts.e)

    round_pos = opts.r
    if round_pos is not None:
        round_pos = int(round_pos)

    chunk_size = opts.chunk_size
    if chunk_size:
        chunk_size = int(chunk_size)

    for input_file in input_files:
        if not exists(input_file):
            sys.stderr.write("The given input file does not exist!\n")
            sys.exit(-78)

    gsh = GenerateScoresHistograms(
        input_files, output_files, scores, xscale, yscale, bins_num, ranges,
        round_pos, chunk_size)
    gsh.generate_scores_histograms(score_columns, start, end)

    sys.stderr.write(
        "The program was running for [h:m:s]: " + str(datetime.timedelta(
            seconds=round(time.time() - start_time, 0))) + "\n")


if __name__ == '__main__':
    main()
