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
from variants.parquet_io import save_ped_df_to_parquet, \
    save_variants_to_parquet
from variants.import_commons import build_contig_regions, \
    contigs_makefile_generate


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
        summary_filename = os.path.join(
            outdir,
            "summary_variants_{}.parquet".format(suffix))
        alleles_filename = os.path.join(
            outdir,
            "family_alleles_{}.parquet".format(suffix))

        save_variants_to_parquet(
            dae.full_variants_iterator(),
            summary_filename,
            alleles_filename)

    except Exception as ex:
        print("unexpected error:", ex)
        traceback.print_exc(file=sys.stdout)
    end = time.time()
    print("DONE converting region {}; time elapsed: {} sec".format(
        region, int(end-start)))


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


def dae_build_region(argv):
    config = Configure.from_dict({
        "dae": {
            'summary_filename': argv.summary,
            'toomany_filename': argv.toomany,
            'family_filename': argv.families
        }})

    # contigs = ['chr21', 'chr22']

    assert argv.out is not None
    parquet_config = Configure.from_prefix_parquet(argv.out).parquet

    genome = get_genome(genome_file=None)

    dae = RawDAE(
        config.dae.summary_filename,
        config.dae.toomany_filename,
        config.dae.family_filename,
        region=argv.region,
        genome=genome,
        annotator=None)

    dae.load_families()

    save_ped_df_to_parquet(
        dae.ped_df,
        parquet_config.pedigree)

    print("going to build: ", argv.region)

    start = time.time()
    save_variants_to_parquet(
        dae.full_variants_iterator(),
        summary_filename=parquet_config.summary_variant,
        family_filename=parquet_config.family_variant,
        effect_gene_filename=parquet_config.effect_gene_variant,
        member_filename=parquet_config.member_variant,
        bucket_index=argv.bucket_index)
    end = time.time()

    print("DONE region: {} for {} sec".format(
        argv.region, round(end-start)))


def dae_build_makefile(argv):

    data_contigs = get_contigs(argv.summary)
    # data_contigs = ['chr21', 'chr22']
    genome = get_genome(genome_file=None)
    build_contigs = build_contig_regions(genome, argv.len)

    contigs_makefile_generate(
        build_contigs,
        data_contigs,
        argv.out,
        'dae2parquet.py region',
        "{family_filename} {summary_filename} {toomany_filename}".format(
            family_filename=argv.families, 
            summary_filename=argv.summary, 
            toomany_filename=argv.toomany)
    )


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
    assert df is not None

    parquet_config = Configure.from_prefix_parquet(argv.out)
    save_ped_df_to_parquet(
        denovo.ped_df,
        parquet_config.parquet.pedigree)


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


def init_transmitted_common(parser):
    parser.add_argument(
        'families', type=str,
        metavar='<pedigree filename>',
        help='families file in pedigree format'
    )
    parser.add_argument(
        'summary', type=str,
        metavar='<summary filename>',
        help=''
    )
    parser.add_argument(
        'toomany', type=str,
        metavar='<toomany filename>',
        help=''
    )
    parser.add_argument(
        '-o', '--out', type=str, default='./',
        dest='out', metavar='output filepath',
        help='output filepath. If none specified, current directory is used'
    )


def init_parser_dae(subparsers):
    parser_dae = subparsers.add_parser('dae')

    init_transmitted_common(parser_dae)

    parser_dae.add_argument(
        '-p', '--processes', type=int, default=4,
        dest='processes_count', metavar='processes count',
        help='number of processes'
    )


def init_parser_region(subparsers):
    parser_region = subparsers.add_parser('region')

    init_transmitted_common(parser_region)

    parser_region.add_argument(
        '--region', type=str,
        dest='region', metavar='region',
        help='region to convert'
    )

    parser_region.add_argument(
        '-b', '--bucket-index', type=int, default=None,
        dest='bucket_index', metavar='bucket index',
        help='bucket index'
    )


def init_parser_make(subparsers):
    parser_region = subparsers.add_parser('make')

    init_transmitted_common(parser_region)

    parser_region.add_argument(
        '--len', type=int,
        default=None,
        dest='len', metavar='len',
        help='split contigs in regions with length <len>'
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
    init_parser_region(subparsers)
    init_parser_make(subparsers)

    parser_args = parser.parse_args(argv)
    return parser_args


if __name__ == "__main__":
    argv = parse_cli_arguments(sys.argv[1:])

    if argv.type == 'denovo':
        denovo_build(argv)
    elif argv.type == 'dae':
        dae_build(argv)
    elif argv.type == 'region':
        dae_build_region(argv)
    elif argv.type == 'make':
        dae_build_makefile(argv)
