import pytest

from box import Box

from ..tools.annotator_config import AnnotationConfigParser
from ..tools.effect_annotator import VariantEffectAnnotator

from .conftest import relative_to_this_test_folder

from dae.backends.vcf.loader import RawVariantsLoader


@pytest.fixture(scope='session')
def effect_annotator():
    options = Box({
        "vcf": True,
        "direct": False,
        'r': 'reference',
        'a': 'alternative',
        'c': 'chrom',
        'p': 'position',

        # "c": "CSHL:chr",
        # "p": "CSHL:position",
        # "v": "CSHL:variant",
    }, default_box=True, default_box_attr=None)

    columns = {
        'effect_type': 'effect_type_1',
        'effect_genes': 'effect_genes_1',
        'effect_gene_genes': 'effect_gene_genes_1',
        'effect_gene_types': 'effect_gene_types_1',
        'effect_details': 'effect_details_1',
        'effect_details_transcript_ids': 'effect_details_transcript_ids_1',
        'effect_details_details': 'effect_details_details_1'
    }

    config = AnnotationConfigParser.parse_section(
        Box({
            'options': options,
            'columns': columns,
            'annotator': 'effect_annotator.VariantEffectAnnotator'
        })
    )

    annotator = VariantEffectAnnotator(config)
    assert annotator is not None

    return annotator


def test_effect_annotator(effect_annotator, variants_io, capsys):
    with variants_io("fixtures/effects_trio_multi-eff.txt") as io_manager:

        captured = capsys.readouterr()

        effect_annotator.annotate_file(io_manager)

    captured = capsys.readouterr()
    print(captured.err)
    print(captured.out)

    print(effect_annotator.schema)


def test_effect_annotator_df(effect_annotator):

    df = RawVariantsLoader.load_annotation_file(
        relative_to_this_test_folder("fixtures/effects_trio_multi-eff.txt")
    )

    columns = [
        'alternative',
        'effect_type',
        'effect_gene_types',
        'effect_gene_genes',
        'effect_details_transcript_ids',
        'effect_details_details',
    ]
    df[columns] = df[columns].fillna('')

    res_df = effect_annotator.annotate_df(df)
    columns += [
        'effect_type_1',
        'effect_gene_types_1',
        'effect_gene_genes_1',
        'effect_details_transcript_ids_1',
        'effect_details_details_1',
    ]

    print(res_df[columns])

    assert list(res_df.effect_type.values) == \
        list(res_df['effect_type_1'].values)

    print(res_df[['effect_gene_genes', 'effect_gene_genes_1']])
    assert list(res_df.effect_gene_genes.values) == \
        list(res_df.effect_gene_genes_1.values)

    print(res_df[['effect_gene_types', 'effect_gene_types_1']])
    assert list(res_df.effect_gene_types.values) == \
        list(res_df.effect_gene_types_1.values)

    # assert list(res_df.effect_details_transcript_ids.values) == \
    #     list(res_df.effect_details_transcript_ids_1.values)
    # assert list(res_df.effect_details_details.values) == \
    #     list(res_df.effect_details_details_1.values)
