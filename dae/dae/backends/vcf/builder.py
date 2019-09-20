import os

from box import Box

from ..configure import Configure

from .raw_vcf import RawFamilyVariants
from .annotate_allele_frequencies import VcfAlleleFrequencyAnnotator
from .loader import RawVariantsLoader

from dae.annotation.tools.annotator_config import AnnotationConfigParser
from dae.annotation.tools.effect_annotator import VariantEffectAnnotator


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


def save_annotation_to_csv(annot_df, filename, sep="\t"):
    def convert_array_of_strings_to_string(a):
        if not a:
            return None
        return RawVariantsLoader.SEP1.join(a)

    vars_df = annot_df.copy()
    vars_df['effect_gene_genes'] = vars_df['effect_gene_genes'].\
        apply(convert_array_of_strings_to_string)
    vars_df['effect_gene_types'] = vars_df['effect_gene_types'].\
        apply(convert_array_of_strings_to_string)
    vars_df['effect_details_transcript_ids'] = \
        vars_df['effect_details_transcript_ids'].\
        apply(convert_array_of_strings_to_string)
    vars_df['effect_details_details'] = \
        vars_df['effect_details_details'].\
        apply(convert_array_of_strings_to_string)
    vars_df.to_csv(
        filename,
        index=False,
        sep=sep
    )


def save_annotation_file(annot_df, filename, sep='\t', storage='csv'):
    assert storage == 'csv'
    if storage == 'csv':
        save_annotation_to_csv(annot_df, filename, sep)
    # elif storage == 'parquet':
    #     save_summary_to_parquet(annot_df, filename)
    #     # vars_df.to_parquet(filename, engine='pyarrow')
    else:
        raise ValueError("unexpected output format: {}".format(storage))


def variants_builder(prefix, genomes_db, force_reannotate=False):
    assert genomes_db is not None

    conf = Configure.from_prefix_vcf(prefix)

    if os.path.exists(conf.vcf.annotation) and not force_reannotate:
        fvars = RawFamilyVariants(conf, genomes_db=genomes_db)
        return fvars

    # effect_annotator = VcfVariantEffectsAnnotator(genome, gene_models)
    freq_annotator = VcfAlleleFrequencyAnnotator()
    effect_annotator = effect_annotator_builder(genomes_db)

    fvars = RawFamilyVariants(
        conf, annotator=freq_annotator, genomes_db=genomes_db
    )
    fvars.annot_df = effect_annotator.annotate_df(fvars.annot_df)

    save_annotation_file(fvars.annot_df, conf.vcf.annotation)

    return fvars
