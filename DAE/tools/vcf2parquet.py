#!/usr/bin/env python

'''
Created on Jun 4, 2018

@author: lubo
'''
from __future__ import print_function

import os
import sys

from RegionOperations import Region
from variants.annotate_allele_frequencies import VcfAlleleFrequencyAnnotator
from variants.annotate_composite import AnnotatorComposite
from variants.annotate_variant_effects import VcfVariantEffectsAnnotator
from variants.builder import get_genome, get_gene_models
from variants.configure import Configure
from variants.parquet_io import family_variants_table,\
    save_family_variants_df_to_parquet, summary_table, save_summary_to_parquet
from variants.raw_vcf import RawFamilyVariants
from cyvcf2 import VCF
import multiprocessing
import functools

import pyarrow.parquet as pq
import pyarrow as pa


def get_contigs(vcf_filename):
    vcf = VCF(vcf_filename)
    return vcf.seqnames


def build_contig(config, contig):
    genome = get_genome(genome_file=None)
    gene_models = get_gene_models(gene_models_file=None)

    effect_annotator = VcfVariantEffectsAnnotator(genome, gene_models)
    freq_annotator = VcfAlleleFrequencyAnnotator()

    annotator = AnnotatorComposite(annotators=[
        effect_annotator,
        freq_annotator
    ])

    fvars = RawFamilyVariants(
        config=config, annotator=annotator, region=contig)

    if fvars.is_empty():
        print("empty contig {} done".format(contig), file=sys.stderr)
        return

    summary_filename = "spark_summary_{}.parquet".format(contig)
    variants_filename = "spark_variants_{}.parquet".format(contig)

    annot_df = fvars.annot_df
    table = summary_table(annot_df)
    assert table is not None

    df = table.to_pandas()
    save_summary_to_parquet(df, summary_filename)

    variants_table = family_variants_table(
        fvars.query_variants(inheritance="not reference"))

    df = variants_table.to_pandas()
    save_family_variants_df_to_parquet(df, variants_filename)
    print("contig {} done".format(contig), file=sys.stderr)


SPARK_CONTIGS = [
    '1',
    '2',
    '3',
    '4',
    '5',
    '6',
    '7',
    '8',
    '9',
    '10',
    '11',
    '12',
    '13',
    '14',
    '15',
    '16',
    '17',
    '18',
    '19',
    '20',
    '21',
    '22',
    'X',
    'Y',
]


def build(argv):
    from variants.default_settings import DATA_DIR

    vcf_filename = os.path.join(DATA_DIR, "spark/spark.vcf.gz")
    ped_filename = os.path.join(DATA_DIR, "spark/spark.ped")

    config = Configure.from_dict({
        "pedigree": ped_filename,
        "vcf": vcf_filename,
        "annotation": None,
    })

    # contigs = ['20', '21', '22']
    contigs = get_contigs(vcf_filename)
    print(contigs)
    genome = get_genome(genome_file=None)
    print(genome.allChromosomes)

    chromosomes = set(genome.allChromosomes)
    for contig in contigs:
        if contig not in chromosomes:
            continue
        assert contig in chromosomes, contig

        print(contig, genome.get_chr_length(contig),
              "groups=", 1 + genome.get_chr_length(contig) / 100000000)

    pool = multiprocessing.Pool(processes=20)
    pool.map(functools.partial(build_contig, config), contigs)


def reindex(argv):
    for contig in SPARK_CONTIGS:
        filename = "spark_summary_{}.parquet".format(contig)
        # filename = "spark_variants_{}.parquet".format(contig)
        parquet_file = pq.ParquetFile(filename)
        print(filename)
        print(parquet_file.metadata)
        print("row_groups:", parquet_file.num_row_groups)
        print(parquet_file.schema)


if __name__ == "__main__":
    # build(sys.argv)
    reindex(sys.argv)
