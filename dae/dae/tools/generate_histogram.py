#!/usr/bin/env python

import argparse
import sys
import time
import datetime
from os.path import exists
import pandas as pd
import numpy as np

from box import Box
import matplotlib as mpl; mpl.use('PS')  # noqa
import matplotlib.pyplot as plt; plt.ioff()  # noqa

import dae.common.config
from dae.configuration.dae_config_parser import CaseSensitiveConfigParser


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

    def __init__(
            self, input_files, score_histograms_info, round_pos=None,
            chunk_size=None, start=None, end=None):
        self.genomic_score_files = input_files
        self.score_histograms_info = score_histograms_info
        self.round_pos = round_pos
        self.chunk_size = chunk_size
        self.start = start
        self.end = end

    def get_variant_length(self, data):
        if self.start is not None and self.end is not None:
            data[self.start] = pd.to_numeric(data[self.start], errors='coerce')
            data[self.end] = pd.to_numeric(data[self.end], errors='coerce')
            data['length'] = data[self.end] - data[self.start]
            data['length'] += 1
            data = data.drop(columns=[self.start, self.end], axis=1)
        else:
            data['length'] = 1

        return data

    def get_empty_bars_and_bins(self, histogram_info):
        bin_num = histogram_info.bin_num

        if histogram_info.xscale == 'linear':
            bins = np.linspace(
                histogram_info.bin_range[0], histogram_info.bin_range[1],
                bin_num)
        elif histogram_info.xscale == 'log':
            bins = []
            min_bin_range = histogram_info.bin_range[0]
            max_bin_range = histogram_info.bin_range[1]
            if histogram_info.bin_range[0] == 0.0:
                step = float(max_bin_range - min_bin_range) / bin_num
                min_bin_range = step / bin_num
                bins = [0.0]
                bin_num -= 1
            print(min_bin_range, max_bin_range)
            bins = bins + list(np.logspace(
                np.log10(min_bin_range), np.log10(max_bin_range), bin_num))

        bars = np.zeros(len(bins) - 1)
        bins = np.array(bins)

        return bars, bins

    def fill_bars(self, histogram_info, values, bars, bins):
        for s, l in zip(values[histogram_info.score_column], values['length']):
            if s < histogram_info.bin_range[0] or\
                    s > histogram_info.bin_range[1]:
                continue
            idx = (np.abs(bins - s)).argmin()
            if idx == histogram_info.bin_num - 1:
                idx -= 1
            bars[idx] += l

        return bars

    def get_bars_and_bins_with_chunking(self, histogram_info, use_columns):
        if not histogram_info.bin_range:
            histogram_info.set_bin_range_from_files(
                self.genomic_score_files, self.chunk_size, self.round_pos)
        bars, bins = self.get_empty_bars_and_bins(histogram_info)

        for genomic_score_file in self.genomic_score_files:
            for chunk in pd.read_csv(
                genomic_score_file, usecols=use_columns, sep='\t',
                    header=histogram_info.header, chunksize=self.chunk_size,
                    low_memory=True):
                chunk = self.get_variant_length(chunk)
                chunk[histogram_info.score_column] = pd.to_numeric(
                    chunk[histogram_info.score_column],
                    errors='coerce')

                bars = self.fill_bars(histogram_info, chunk, bars, bins)

        return (bars, bins)

    def get_bars_and_bins_without_chunking(self, histogram_info, use_columns):
        values = pd.DataFrame(columns=[histogram_info.score_column])

        for genomic_score_file in self.genomic_score_files:
            v = pd.read_csv(
                genomic_score_file, usecols=use_columns, sep='\t',
                header=histogram_info.header)
            v = self.get_variant_length(v)
            v[histogram_info.score_column] = pd.to_numeric(
                v[histogram_info.score_column], errors='coerce')
            v = pd.DataFrame(v)
            values = pd.concat([values, v], sort=True)

        if not histogram_info.bin_range:
            histogram_info.set_bin_range_from_values(values, self.round_pos)
        bars, bins = self.get_empty_bars_and_bins(histogram_info)

        # bars = self.fill_bars(histogram_info, values, bars, bins)
        bars, bins = np.histogram(
            values[histogram_info.score_column].values, bins=bins,
            range=histogram_info.bin_range)

        return (bars, bins)

    def save_histogram(self, bars, bins, histogram_info):
        scores = pd.Series(bins, name='scores')
        data = pd.Series(bars, name=histogram_info.score)
        histogram = pd.concat([data, scores], axis=1, sort=True)
        histogram.to_csv(histogram_info.output_file, index=False)

        histogram.dropna(inplace=True)
        bins = list(histogram['scores'].values)
        bars = list(map(int, histogram[histogram_info.score].values))
        fig, ax = plt.subplots()
        plt.yscale(histogram_info.yscale)
        ax.bar(bins, bars, width=0.01)
        plt.savefig(histogram_info.output_file + '.png')

    def generate_scores_histograms(self):
        for histogram_info in self.score_histograms_info:
            use_columns = [histogram_info.score_column]
            if self.start is not None and self.end is not None:
                use_columns.extend([self.start, self.end])

            if self.chunk_size:
                bars, bins = self.get_bars_and_bins_with_chunking(
                    histogram_info, use_columns)
            else:
                bars, bins = self.get_bars_and_bins_without_chunking(
                    histogram_info, use_columns)

            self.save_histogram(bars, bins, histogram_info)

            print('Generating {} finished'.format(histogram_info.score))


class ScoreHistogramInfo(object):

    def __init__(
            self, score, score_column, output_file, xscale, yscale, bin_num,
            bin_range=None):
        self.score = score
        self.score_column = score_column
        self.output_file = output_file
        self.xscale = xscale
        self.yscale = yscale
        self.bin_num = bin_num
        self.bin_range = bin_range

        self.header = 'infer' if type(self.score_column) is not int else None

    def set_bin_range(self, min_value, max_value, round_pos):
        if round_pos is not None:
            min_value = np.around(min_value, round_pos)
            max_value = np.around(max_value, round_pos)

        self.bin_range = [min_value, max_value]

    def set_bin_range_from_files(self, filenames, chunk_size, round_pos):
        min_value = None
        max_value = None

        for filename in filenames:
            for chunk in pd.read_csv(
                filename, usecols=[self.score_column], sep='\t',
                    header=self.header, chunksize=chunk_size,
                    low_memory=True):
                chunk[self.score_column] = pd.to_numeric(
                    chunk[self.score_column], errors='coerce')
                min_chunk = chunk[self.score_column].min()
                max_chunk = chunk[self.score_column].max()

                if min_value is None or min_chunk < min_value:
                    min_value = min_chunk
                if max_value is None or max_chunk > max_value:
                    max_value = max_chunk

        self.set_bin_range(min_value, max_value, round_pos)

    def set_bin_range_from_values(self, values, round_pos):
        min_value = values[self.score].min()
        max_value = values[self.score].max()

        self.set_bin_range(min_value, max_value, round_pos)


def main():
    start_time = time.time()

    opts = get_argument_parser().parse_args()

    config = CaseSensitiveConfigParser()
    config.read(opts.config)
    config = Box(dae.common.config.to_dict(config),
                 default_box=True, default_box_attr=None)

    score_histograms_info = []

    scores = config.genomicScores.scores.split(',')

    score_columns = opts.scores
    if score_columns is not None:
        score_columns = [int(el) if el.isdigit() else el
                         for el in score_columns.split(',')]
    else:
        score_columns = scores

    for score, score_column in zip(scores, score_columns):
        histogram_info = config['genomicScores.{}'.format(score)]

        if histogram_info.range:
            bin_range = list(map(float, histogram_info.bin_range.split(',')))
        else:
            bin_range = None

        score_histograms_info.append(ScoreHistogramInfo(
            score, score_column, histogram_info.file, histogram_info.xscale,
            histogram_info.yscale, int(histogram_info.bins), bin_range))

    if opts.infile == '-':
        sys.stderr.write("You must provide input file!\n")
        sys.exit(-78)

    input_files = opts.infile.split(',')

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
        input_files, score_histograms_info, round_pos, chunk_size, start, end)
    gsh.generate_scores_histograms()

    sys.stderr.write(
        "The program was running for [h:m:s]: " + str(datetime.timedelta(
            seconds=round(time.time() - start_time, 0))) + "\n")


if __name__ == '__main__':
    main()
