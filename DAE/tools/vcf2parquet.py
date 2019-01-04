#!/usr/bin/env python

'''
Created on Jun 4, 2018

@author: lubo
'''
from __future__ import print_function

import os
import sys
import argparse

from variants.annotate_allele_frequencies import VcfAlleleFrequencyAnnotator
from variants.annotate_composite import AnnotatorComposite
from variants.annotate_variant_effects import VcfVariantEffectsAnnotator
from variants.builder import get_genome, get_gene_models
from variants.configure import Configure
from variants.parquet_io import save_family_variants_to_parquet, \
    save_summary_variants_to_parquet, \
    save_ped_df_to_parquet
from variants.raw_vcf import RawFamilyVariants
from cyvcf2 import VCF
import multiprocessing
import functools


def get_contigs(vcf_filename):
    vcf = VCF(vcf_filename)
    return vcf.seqnames


def create_vcf_variants(
        config, region=None, genome_file=None, gene_models_file=None):

    genome = get_genome(genome_file=genome_file)
    gene_models = get_gene_models(gene_models_file=gene_models_file)

    effect_annotator = VcfVariantEffectsAnnotator(genome, gene_models)
    freq_annotator = VcfAlleleFrequencyAnnotator()

    annotator = AnnotatorComposite(annotators=[
        effect_annotator,
        freq_annotator
    ])

    fvars = RawFamilyVariants(
        config=config, annotator=annotator,
        region=region)
    return fvars


def import_vcf_contig(config, contig):
    # region = "{}:1-100000".format(contig)
    region = contig
    fvars = create_vcf_variants(config, region)

    if fvars.is_empty():
        print("empty contig {} done".format(contig), file=sys.stderr)
        return
    raise NotImplementedError()
    
    # summary_filename = os.path.join(
    #     config.output,
    #     "summary_variants_{}.parquet".format(contig))
    # allele_filename = os.path.join(
    #     config.output,
    #     "family_alleles_{}.parquet".format(contig))

    # save_summary_variants_to_parquet(
    #     fvars.query_variants(),
    #     summary_filename)
    # save_family_variants_to_parquet(
    #     fvars.query_variants(),
    #     allele_filename)
    # print("contig {} done".format(contig), file=sys.stderr)


def import_pedigree(config):
    pedigree_filename = os.path.join(
        config.output,
        "pedigree.parquet",
    )
    region = "1:1-100000"
    fvars = create_vcf_variants(config, region)
    save_ped_df_to_parquet(fvars.ped_df, pedigree_filename)


def import_vcf(argv):
    assert os.path.exists(argv.vcf)
    assert os.path.exists(argv.pedigree)
    assert os.path.exists(argv.out)
    assert os.path.isdir(argv.out)

    vcf_filename = argv.vcf
    ped_filename = argv.pedigree

    config = Configure.from_dict({
            'vcf': {
                'pedigree': ped_filename,
                'vcf': vcf_filename,
                'annotation': None,
            },
            'output': argv.out,
        })

    contigs = get_contigs(vcf_filename)
    genome = get_genome(genome_file=None)

    chromosomes = set(genome.allChromosomes)
    contigs_to_process = []
    for contig in contigs:
        if contig not in chromosomes:
            continue
        assert contig in chromosomes, contig

        print(contig, genome.get_chr_length(contig),
              "groups=", 1 + genome.get_chr_length(contig) / 100000000)
        contigs_to_process.append(contig)

    import_pedigree(config)

    pool = multiprocessing.Pool(processes=argv.processes_count)
    pool.map(
        functools.partial(import_vcf_contig, config),
        contigs_to_process)


def parse_cli_arguments(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Convert VCF file to parquet')

    parser.add_argument(
        'pedigree', type=str,
        metavar='<pedigree filename>',
        help='families file in pedigree format'
    )
    parser.add_argument(
        'vcf', type=str,
        metavar='<VCF filename>',
        help='VCF file to import'
    )
    parser.add_argument(
        '-o', '--out', type=str, default='./',
        dest='out', metavar='output filepath',
        help='output filepath. If none specified, current directory is used'
    )
    parser.add_argument(
        '-p', '--processes', type=int, default=4,
        dest='processes_count', metavar='processes count',
        help='number of processes'
    )

    parser_args = parser.parse_args(argv)
    return parser_args


# def reindex(argv):
#     for contig in SPARK_CONTIGS:
#         filename = "spark_summary_{}.parquet".format(contig)
#         # filename = "spark_variants_{}.parquet".format(contig)
#         parquet_file = pq.ParquetFile(filename)
#         print(filename)
#         print(parquet_file.metadata)
#         print("row_groups:", parquet_file.num_row_groups)
#         print(parquet_file.schema)


if __name__ == "__main__":
    argv = parse_cli_arguments(sys.argv[1:])
    print(argv)

    import_vcf(argv)
    # reindex(sys.argv)
