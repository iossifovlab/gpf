import pytest

from box import Box

from ..tools.annotator_config import VariantAnnotatorConfig
from ..tools.effect_annotator import VariantEffectAnnotator
from ..tools.schema import Schema

from .conftest import relative_to_this_test_folder

from backends.vcf.loader import RawVariantsLoader


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

    columns_config = {
        'effect_type': 'effect_type_1',
        'effect_genes': 'effect_genes_1',
        'effect_gene_genes': 'effect_gene_genes_1',
        'effect_gene_types': 'effect_gene_types_1',
        'effect_details': 'effect_details_1',
        'effect_details_transcript_ids': 'effect_details_transcript_ids_1',
        'effect_details_details': 'effect_details_details_1'
    }

    config = VariantAnnotatorConfig(
        name="test_annotator",
        annotator_name="effect_annotator.VariantEffectAnnotator",
        options=options,
        columns_config=columns_config,
        virtuals=[]
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
    # print(df)
    print(Schema.from_df(df))

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


def test_schema_experiment():
    # df = pd.read_csv(
    #     relative_to_this_test_folder("fixtures/effects_trio_multi-eff.txt"),
    #     dtype={
    #         'chrom': str,
    #         'position': np.int32,
    #     },
    #     sep='\t')

    filename = relative_to_this_test_folder(
        "fixtures/effects_trio_multi-eff.txt")
    df = RawVariantsLoader.load_annotation_file(filename)
    print(df)
    print(Schema.from_df(df))
