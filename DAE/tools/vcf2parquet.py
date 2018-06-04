#!/usr/bin/env python

'''
Created on Jun 4, 2018

@author: lubo
'''
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


def contigs(vcf_filename):
    vcf = VCF(vcf_filename)
    return vcf.seqnames


def build_contig(contig, config):
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


def main(argv):
    from variants.default_settings import DATA_DIR

    vcf_filename = os.path.join(DATA_DIR, "spark/spark.vcf.gz")
    ped_filename = os.path.join(DATA_DIR, "spark/spark.ped")

    # region = "1:0-100000000"
    contig = "21"

    config = Configure.from_dict({
        "pedigree": ped_filename,
        "vcf": vcf_filename,
        "annotation": None,
    })

    build_contig(contig, config)


if __name__ == "__main__":
    main(sys.argv)
