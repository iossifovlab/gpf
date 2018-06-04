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
    save_family_variants_df_to_parquet
from variants.raw_vcf import RawFamilyVariants


def main(argv):
    from variants.default_settings import DATA_DIR

    vcf_filename = os.path.join(DATA_DIR, "spark/spark.vcf.gz")
    ped_filename = os.path.join(DATA_DIR, "spark/spark.ped")
    summary_filename = os.path.join(DATA_DIR, "spark/spark_summary.parquet")

    # region = Region("1", 0, 100000000)
    region = "1:0-100000000"

    config = Configure.from_dict({
        "pedigree": ped_filename,
        "vcf": vcf_filename,
        "annotation": summary_filename,
    })

    genome = get_genome(genome_file=None)
    gene_models = get_gene_models(gene_models_file=None)

    effect_annotator = VcfVariantEffectsAnnotator(genome, gene_models)
    freq_annotator = VcfAlleleFrequencyAnnotator()

    annotator = AnnotatorComposite(annotators=[
        effect_annotator,
        freq_annotator
    ])

    fvars = RawFamilyVariants(
        config=config, annotator=annotator, region=region)

    variants_table = family_variants_table(
        fvars.query_variants(inheritance="not reference"))

    df = variants_table.to_pandas()
    print(df.head())

    save_family_variants_df_to_parquet(df, "spark_variants.parquet")


if __name__ == "__main__":
    main(sys.argv)
