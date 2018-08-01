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

from variants.builder import get_genome
from variants.configure import Configure
from variants.raw_dae import RawDAE, RawDenovo
import traceback
from variants.parquet_io import save_family_variants_to_parquet,\
    save_ped_df_to_parquet, save_summary_variants_to_parquet


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

        save_summary_variants_to_parquet(
            dae.wrap_summary_variants(df),
            summary_filename)

        save_family_variants_to_parquet(
            dae.wrap_family_variants(df),
            variants_filename,
            alleles_filename)

    except Exception as ex:
        print("unexpected error:", ex)
        traceback.print_exc(file=sys.stdout)

    print("DONE converting contig {}".format(contig))


def dae_build(argv):

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
        "out/w1202s766e611/pedigree.parquet")

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
        outprefix="out/w1202s766e611")

    pool = multiprocessing.Pool(processes=15)
    pool.map(converter, build_contigs)


def denovo_build(argv):
    prefix = os.path.join(
        os.environ.get("DAE_DB_DIR"), 'cccc/IossifovWE2014/')
    config = Configure.from_dict({
        "denovo": {
            'denovo_filename': os.path.join(
                prefix, 'Supplement-T2-eventsTable-annot.txt'),
            'family_filename': os.path.join(
                prefix, 'familyInfo.txt'),
        }})

    genome = get_genome()

    denovo = RawDenovo(
        config.denovo.denovo_filename,
        config.denovo.family_filename,
        genome=genome,
        annotator=None)

    denovo.load_families()
    df = denovo.load_denovo_variants()

    parquet_config = Configure.from_prefix_parquet("out/IossifovWE2014/")
    save_ped_df_to_parquet(
        denovo.ped_df,
        parquet_config.parquet.pedigree)

    save_summary_variants_to_parquet(
        denovo.wrap_summary_variants(df),
        parquet_config.parquet.summary_variants)

    save_family_variants_to_parquet(
        denovo.wrap_family_variants(df),
        parquet_config.parquet.family_variants,
        parquet_config.parquet.family_alleles)


if __name__ == "__main__":
    dae_build(sys.argv)
