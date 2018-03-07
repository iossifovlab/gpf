'''
Created on Mar 6, 2018

@author: lubo
'''
from __future__ import print_function

import numpy as np
import pandas as pd

from variant_annotation.annotator import VariantAnnotator
from DAE import genomesDB
from variant_annotation.variant import Variant


GA = genomesDB.get_genome()  # @UndefinedVariable
gmDB = genomesDB.get_gene_models()  # @UndefinedVariable


class VariantEffectsAnnotator(object):

    def __init__(self, genome=GA, gene_models=gmDB):
        self.variant_annotator = VariantAnnotator(
            reference_genome=genome,
            gene_models=gene_models,
        )
        assert self.variant_annotator is not None

    def annotate_variant(self, vcf_variant):
        result = []
        for alt in vcf_variant.ALT:
            variant = Variant(
                chrom=vcf_variant.CHROM,
                position=vcf_variant.start,
                ref=vcf_variant.REF,
                alt=alt)
            effects = self.variant_annotator.annotate(variant)
            result.append(self.variant_annotator.effect_description(effects))
        return result

    def annotate(self, vars_df, vcf_vars):
        effect_types = pd.Series(index=vars_df.index, dtype=np.object_)
        effect_genes = pd.Series(index=vars_df.index, dtype=np.object_)
        effect_details = pd.Series(index=vars_df.index, dtype=np.object_)

        for index, v in enumerate(vcf_vars):
            effects = self.annotate_variant(v)
            effects = np.array(effects)
            effect_types[index] = effects[:, 0]
            effect_genes[index] = effects[:, 1]
            effect_details[index] = effects[:, 2]

        vars_df['effectType'] = effect_types
        vars_df['effectGene'] = effect_genes
        vars_df['effectDetails'] = effect_details

        return vars_df
