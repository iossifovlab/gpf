#!/usr/bin/env python

'''
Created on Jul 23, 2018

@author: lubo
'''
from __future__ import print_function

import functools
import multiprocessing
import os
import sys

import pysam

import pyarrow.parquet as pq
from variants.builder import get_genome
from variants.configure import Configure
from variants.raw_dae import RawDAE
import traceback
from variants.parquet_io import save_family_variants_to_parquet


def get_contigs(tabixfilename):
    with pysam.Tabixfile(tabixfilename) as tbx:  # @UndefinedVariable
        return tbx.contigs


def convert_contig(contig, outprefix=None, config=None,):
    try:
        print("converting contig {} to {}".format(contig, outprefix))
        print(config)

        assert isinstance(config, Configure)
        assert os.path.exists(config.dae.summary_filename)
        assert os.path.exists(config.dae.toomany_filename)
        assert os.path.exists(config.dae.family_filename)

        genome = get_genome()

        dae = RawDAE(
            config.dae.summary_filename,
            config.dae.toomany_filename,
            config.dae.family_filename,
            region=contig,
            genome=genome,
            annotator=None)

        dae.load_families()

        df = dae.load_family_variants()

        out = {"prefix": outprefix, "contig": contig}

        summary_filename = "{prefix}_summary_variants_{contig}.parquet".format(
            **out)
        variants_filename = "{prefix}_family_variants_{contig}.parquet".format(
            **out)
        alleles_filename = "{prefix}_family_alleles_{contig}.parquet".format(
            **out)

        summary_table = dae.summary_table(df)
        pq.write_table(summary_table, summary_filename)
        summary_table = None

        save_family_variants_to_parquet(
            dae.wrap_family_variants(df),
            variants_filename,
            alleles_filename)

    except Exception as ex:
        print("unexpected error:", ex)
        traceback.print_exc(file=sys.stdout)

    print("DONE converting contig {}".format(contig))


def build(argv):

    prefix = os.path.join(
        os.environ.get("DAE_DB_DIR"), 'cccc/w1202s766e611')
    config = Configure.from_dict({
        "dae": {
            'summary_filename': os.path.join(
                prefix, 'transmissionIndex-HW-DNRM.txt.bgz'),
            'toomany_filename': os.path.join(
                prefix, 'transmissionIndex-HW-DNRM-TOOMANY.txt.bgz'),
            'family_filename': os.path.join(
                prefix, 'familyInfo.txt'),
        }})

    contigs = get_contigs(config.dae.summary_filename)
    print(contigs)
    genome = get_genome(genome_file=None)
    print(genome.allChromosomes)

    chromosomes = set(genome.allChromosomes)

    # contigs = ['21', '22']

    build_contigs = []
    for contig in contigs:
        if contig not in chromosomes:
            continue
        assert contig in chromosomes, contig
        print(contig, genome.get_chr_length(contig),
              "groups=", 1 + genome.get_chr_length(contig) / 100000000)
        build_contigs.append(contig)

    print("going to build: ", build_contigs)

    converter = functools.partial(
        convert_contig,
        config=config,
        outprefix="out_no_reference/w1202s766e611")

    pool = multiprocessing.Pool(processes=20)
    pool.map(converter, build_contigs)


if __name__ == "__main__":
    build(sys.argv)
