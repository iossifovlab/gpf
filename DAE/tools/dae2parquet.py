#!/usr/bin/env python

'''
Created on Jul 23, 2018

@author: lubo
'''
from __future__ import print_function
from collections import OrderedDict

import functools
import multiprocessing
import os
import sys
import time

import pysam
import argparse

from RegionOperations import Region

from variants.builder import get_genome
from variants.configure import Configure
from variants.raw_dae import RawDAE, RawDenovo
import traceback
from variants.parquet_io import save_family_variants_to_parquet,\
    save_ped_df_to_parquet, save_summary_variants_to_parquet


def get_contigs(tabixfilename):
    with pysam.Tabixfile(tabixfilename) as tbx:  # @UndefinedVariable
        return tbx.contigs


def import_transmitted_region(region_spec, outdir, config):
    region, suffix = region_spec
    start = time.time()
    try:
        print("converting contig {} to {}".format(region, outdir))
        print(config)

        assert isinstance(config, Configure)
        assert os.path.exists(config.dae.summary_filename)
        assert os.path.exists(config.dae.toomany_filename)
        assert os.path.exists(config.dae.family_filename)

        region = "{}:{}-{}".format(region.chrom, region.start, region.end)
        genome = get_genome()

        dae = RawDAE(
            config.dae.summary_filename,
            config.dae.toomany_filename,
            config.dae.family_filename,
            region=region,
            genome=genome,
            annotator=None)

        dae.load_families()
        df = dae.load_family_variants()
        if len(df) == 0:
            print("DONE EMTPY region {}".format(region))
            return
        summary_filename = os.path.join(
            outdir,
            "summary_variants_{}.parquet".format(suffix))
        alleles_filename = os.path.join(
            outdir,
            "family_alleles_{}.parquet".format(suffix))

        save_summary_variants_to_parquet(
            dae.wrap_summary_variants(df),
            summary_filename)

        save_family_variants_to_parquet(
            dae.wrap_family_variants(df),
            alleles_filename)

    except Exception as ex:
        print("unexpected error:", ex)
        traceback.print_exc(file=sys.stdout)
    end = time.time()
    print("DONE converting region {}; time elapsed: {} sec".format(
        region, int(end-start)))


def build_contig_regions(genome, TRANSMITTED_STEP=10000000):
    contigs = OrderedDict(genome.get_all_chr_lengths())
    contig_parts = OrderedDict([
        (contig, int(size / TRANSMITTED_STEP + 1))
        for contig, size in contigs.items()
    ])
    contig_regions = OrderedDict()
    for contig, size in contigs.items():
        regions = []
        total_parts = contig_parts[contig]
        step = int(size / total_parts + 1)
        for index in range(total_parts):
            begin_pos = index * step
            end_pos = (index + 1) * step - 1
            if index + 1 == total_parts:
                end_pos = size
            region = Region(contig, begin_pos, end_pos)
            regions.append(region)
        contig_regions[contig] = regions
    return contig_regions


def dae_build(argv):
    config = Configure.from_dict({
        "dae": {
            'summary_filename': argv.summary,
            'toomany_filename': argv.toomany,
            'family_filename': argv.families
        }})

    contigs = get_contigs(config.dae.summary_filename)
    # contigs = ['chr21', 'chr22']

    genome = get_genome(genome_file=None)
    contig_regions = build_contig_regions(genome)

    dae = RawDAE(
        config.dae.summary_filename,
        config.dae.toomany_filename,
        config.dae.family_filename,
        region=None,
        genome=genome,
        annotator=None)

    dae.load_families()
    save_ped_df_to_parquet(
        dae.ped_df,
        os.path.join(argv.out, 'pedigree.parquet'))

    build_regions = []
    for contig_index, contig in enumerate(contigs):
        if contig not in contig_regions:
            continue
        assert contig in contig_regions, contig
        for part, region in enumerate(contig_regions[contig]):
            suffix = "-{:0>3}-{:0>3}-{}".format(
                contig_index, part, contig
            )
            build_regions.append((region, suffix))

    print("going to build: ", len(build_regions))

    converter = functools.partial(
        import_transmitted_region,
        config=config,
        outdir=argv.out)

    pool = multiprocessing.Pool(processes=argv.processes_count)
    pool.map(converter, build_regions)


def denovo_build(argv):
    config = Configure.from_dict({
        "denovo": {
            'denovo_filename': argv.variants,
            'family_filename': argv.families
        }})

    genome = get_genome()

    denovo = RawDenovo(
        config.denovo.denovo_filename,
        config.denovo.family_filename,
        genome=genome,
        annotator=None)

    denovo.load_families()
    df = denovo.load_denovo_variants()

    parquet_config = Configure.from_prefix_parquet(argv.out)
    save_ped_df_to_parquet(
        denovo.ped_df,
        parquet_config.parquet.pedigree)

    save_summary_variants_to_parquet(
        denovo.wrap_summary_variants(df),
        parquet_config.parquet.summary_variants)

    save_family_variants_to_parquet(
        denovo.wrap_family_variants(df),
        parquet_config.parquet.family_alleles)


def init_parser_denovo(subparsers):
    parser_denovo = subparsers.add_parser('denovo')

    parser_denovo.add_argument(
        'variants', type=str,
        metavar='<variants filename>',
        help='annotated variants file'
    )
    parser_denovo.add_argument(
        'families', type=str,
        metavar='<pedigree filename>',
        help='families file in pedigree format'
    )
    parser_denovo.add_argument(
        '-o', '--out', type=str, default='./',
        dest='out', metavar='output filepath',
        help='output filepath. If none specified, current directory is used'
    )


def init_parser_dae(subparsers):
    parser_dae = subparsers.add_parser('dae')

    parser_dae.add_argument(
        'families', type=str,
        metavar='<pedigree filename>',
        help='families file in pedigree format'
    )
    parser_dae.add_argument(
        'summary', type=str,
        metavar='<summary filename>',
        help=''
    )
    parser_dae.add_argument(
        'toomany', type=str,
        metavar='<toomany filename>',
        help=''
    )
    parser_dae.add_argument(
        '-o', '--out', type=str, default='./',
        dest='out', metavar='output filepath',
        help='output filepath. If none specified, current directory is used'
    )
    parser_dae.add_argument(
        '-p', '--processes', type=int, default=4,
        dest='processes_count', metavar='processes count',
        help='number of processes'
    )


def parse_cli_arguments(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Convert DAE file to parquet')

    subparsers = parser.add_subparsers(
        dest='type',
        title='subcommands',
        description='choose what type of data to convert',
        help='denovo or transmitted study')

    init_parser_denovo(subparsers)
    init_parser_dae(subparsers)

    parser_args = parser.parse_args(argv)
    return parser_args


if __name__ == "__main__":
    argv = parse_cli_arguments(sys.argv[1:])

    if argv.type == 'denovo':
        denovo_build(argv)
    elif argv.type == 'dae':
        dae_build(argv)
