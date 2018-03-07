'''
Created on Mar 6, 2018

@author: lubo
'''
from __future__ import print_function

from DAE import genomesDB
import numpy as np
from variant_annotation.annotator import VariantAnnotator
from variant_annotation.variant import Variant
from variants.annotate_composite import AnnotatorBase


GA = genomesDB.get_genome()  # @UndefinedVariable
gmDB = genomesDB.get_gene_models()  # @UndefinedVariable


class VcfVariantEffectsAnnotator(AnnotatorBase):
    COLUMNS = ['effectType', 'effectGene', 'effectDetails']

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
        result = np.array(result)
        return result[:, 0], result[:, 1], result[:, 2]
