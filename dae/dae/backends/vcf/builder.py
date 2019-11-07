import os

from box import Box

from ..configure import Configure

from .raw_vcf import RawVcfVariants
from .annotate_allele_frequencies import VcfAlleleFrequencyAnnotator
from dae.backends.vcf.loader import RawVcfLoader

from dae.annotation.tools.annotator_config import AnnotationConfigParser
from dae.annotation.tools.effect_annotator import VariantEffectAnnotator
from dae.pedigrees.pedigree_reader import PedigreeReader


def effect_annotator_builder(genomes_db):
    options = Box({
        'vcf': True,
        'direct': False,
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
            'annotator': 'effect_annotator.VariantEffectAnnotator'
        }),
        genomes_db
    )

    annotator = VariantEffectAnnotator(config)

    assert annotator is not None

    return annotator


def variants_builder(prefix, genomes_db, force_reannotate=False):
    assert genomes_db is not None

    conf = Configure.from_prefix_vcf(prefix)

    if os.path.exists(conf.vcf.annotation) and not force_reannotate:
        fvars = RawVcfLoader.load_raw_vcf_variants(
            conf.vcf.pedigree, conf.vcf.vcf, conf.vcf.annotation
        )
        return fvars

    effect_annotator = effect_annotator_builder(genomes_db)

    fvars = RawVcfLoader.load_raw_vcf_variants(
        conf.vcf.pedigree, conf.vcf.vcf
    )
    fvars.annot_df = effect_annotator.annotate_df(fvars.annot_df)
    RawVcfLoader.save_annotation_file(fvars.annot_df, conf.vcf.annotation)

    return fvars
