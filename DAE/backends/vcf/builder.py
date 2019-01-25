'''
Created on Mar 19, 2018

@author: lubo
'''
from __future__ import print_function, unicode_literals, absolute_import

import os

from GeneModelFiles import load_gene_models

from ..configure import Configure

from .raw_vcf import RawFamilyVariants
from .annotate_variant_effects import VcfVariantEffectsAnnotator
from .annotate_allele_frequencies import VcfAlleleFrequencyAnnotator
from .annotate_composite import AnnotatorComposite
from .loader import RawVariantsLoader


def get_genome(genome_file=None):
    if genome_file is not None:
        assert os.path.exists(genome_file)
        from GenomeAccess import openRef
        return openRef(genome_file)
    else:
        from DAE import genomesDB
        return genomesDB.get_genome()  # @UndefinedVariable


def get_gene_models(gene_models_file=None):
    if gene_models_file is not None:
        assert os.path.exists(gene_models_file)
        return load_gene_models(gene_models_file)
    else:
        from DAE import genomesDB
        return genomesDB.get_gene_models()  # @UndefinedVariable


def variants_builder(prefix, genome_file=None, gene_models_file=None):
    conf = Configure.from_prefix_vcf(prefix)
    print(conf)

    if os.path.exists(conf.vcf.annotation):
        fvars = RawFamilyVariants(conf)
        return fvars

    genome = get_genome(genome_file)
    gene_models = get_gene_models(gene_models_file)

    effect_annotator = VcfVariantEffectsAnnotator(genome, gene_models)
    freq_annotator = VcfAlleleFrequencyAnnotator()

    annotator = AnnotatorComposite(annotators=[
        effect_annotator,
        freq_annotator
    ])
    fvars = RawFamilyVariants(conf, annotator=annotator)
    RawVariantsLoader.save_annotation_file(fvars.annot_df, conf.vcf.annotation)

    return fvars
