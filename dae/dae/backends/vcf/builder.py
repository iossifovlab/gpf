'''
Created on Mar 19, 2018

@author: lubo
'''
import os

from box import Box

from dae.GeneModelFiles import load_gene_models

from ..configure import Configure

from .raw_vcf import RawFamilyVariants
from .annotate_allele_frequencies import VcfAlleleFrequencyAnnotator
from .loader import RawVariantsLoader

from dae.annotation.tools.annotator_config import AnnotationConfigParser
from dae.annotation.tools.effect_annotator import VariantEffectAnnotator


def get_genome(genome_file=None):
    if genome_file is not None:
        assert os.path.exists(genome_file)
        from dae.GenomeAccess import openRef
        return openRef(genome_file)
    else:
        from dae.DAE import genomesDB
        return genomesDB.get_genome()  # @UndefinedVariable


def get_gene_models(gene_models_file=None):
    if gene_models_file is not None:
        assert os.path.exists(gene_models_file)
        return load_gene_models(gene_models_file)
    else:
        from dae.DAE import genomesDB
        return genomesDB.get_gene_models()  # @UndefinedVariable


def effect_annotator_builder(
        genome_file=None, gene_models_file=None,
        genome=None, gene_models=None,):
    options = Box({
        "vcf": True,
        "direct": False,
        'r': 'reference',
        'a': 'alternative',
        'c': 'chrom',
        'p': 'position',
    }, default_box=True, default_box_attr=None)

    columns = {
        'effect_type': 'effect_type',
        'effect_genes': 'effect_genes',
        'effect_gene_genes': 'effect_gene_genes',
        'effect_gene_types': 'effect_gene_types',
        'effect_details': 'effect_details',
        'effect_details_transcript_ids': 'effect_details_transcript_ids',
        'effect_details_details': 'effect_details_details'
    }

    config = AnnotationConfigParser.parse_section(
        Box({
            'options': options,
            'columns': columns,
            'annotator': 'effect_annotator.VariantEffectAnnotator',
        })
    )

    annotator = VariantEffectAnnotator(
        config,
        genome_file=genome_file, genome=genome,
        gene_models_file=gene_models_file, gene_models=gene_models)

    assert annotator is not None

    return annotator


def variants_builder(
        prefix, genome_file=None, gene_models_file=None,
        genome=None, gene_models=None,
        force_reannotate=False):

    conf = Configure.from_prefix_vcf(prefix)

    if os.path.exists(conf.vcf.annotation) and not force_reannotate:
        fvars = RawFamilyVariants(conf)
        return fvars

    if genome is None:
        genome = get_genome(genome_file)
    if gene_models is None:
        gene_models = get_gene_models(gene_models_file)

    # effect_annotator = VcfVariantEffectsAnnotator(genome, gene_models)
    freq_annotator = VcfAlleleFrequencyAnnotator()
    effect_annotator = effect_annotator_builder(
        genome_file=genome_file, genome=genome,
        gene_models_file=gene_models_file, gene_models=gene_models)

    fvars = RawFamilyVariants(conf, annotator=freq_annotator)
    fvars.annot_df = effect_annotator.annotate_df(fvars.annot_df)

    RawVariantsLoader.save_annotation_file(fvars.annot_df, conf.vcf.annotation)

    return fvars
