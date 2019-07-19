from __future__ import print_function, absolute_import

import pytest

import pandas as pd
import numpy as np

from box import Box

from ..tools.annotator_config import VariantAnnotatorConfig
from ..tools.effect_annotator import EffectAnnotator, VariantEffectAnnotator
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
        'effect_type': 'effect_type',
        'effect_gene': 'effect_genes',
        'effect_details': 'effect_details'
    }

    config = VariantAnnotatorConfig(
        name="test_annotator",
        annotator_name="effect_annotator.EffectAnnotator",
        options=options,
        columns_config=columns_config,
        virtuals=[]
    )

    annotator = EffectAnnotator(config)
    assert annotator is not None

    return annotator


@pytest.fixture(scope='session')
def variant_effect_annotator():
    options = Box({
        "direct": False,
        "vcf": True,
        'r': 'reference',
        'a': 'alternative',
        'c': 'chrom',
        'p': 'position',
    }, default_box=True, default_box_attr=None)

    columns_config = {
        'effect_type': 'effect_type',

        'effect_genes': 'effect_genes',
        'effect_gene_genes': 'effect_gene_genes',
        'effect_gene_types': 'effect_gene_types',

        'effect_details': 'effect_details',
        'effect_details_transcript_ids': 'effect_details_transcript_ids',
        'effect_details_genes': 'effect_details_genes',
        'effect_details_details': 'effect_details_details',
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


def test_effect_annotator_df(variant_effect_annotator):
    df = pd.read_csv(
        relative_to_this_test_folder("fixtures/effects_trio_multi-eff.txt"),
        dtype={
            'chrom': str,
            'position': np.int32,
        },
        sep='\t')

    columns = [
        'alternative',
        'effect_type',
        'effect_gene_types',
        'effect_gene_genes',
        'effect_details_transcript_ids',
        # 'effect_details_genes',
        'effect_details_details'
    ]
    df[columns] = df[columns].fillna('')
    print(df[[
        'effect_type',
        'effect_gene_types', 'effect_gene_genes',
    ]])

    res_df = variant_effect_annotator.annotate_df(df)
    print(res_df[[
        'effect_type',
        'effect_gene_types', 'effect_gene_genes',
    ]])

    assert list(res_df.effect_type.values) == list(df['effect_type'].values)


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


def test_effect_annotators_compare(
        effect_annotator, variant_effect_annotator, variants_io, capsys):
    assert effect_annotator is not None
    assert variant_effect_annotator is not None
    df = pd.read_csv(
        relative_to_this_test_folder("fixtures/effects_trio_multi-eff.txt"),
        dtype={
            'chrom': str,
            'position': np.int32,
        },
        sep='\t')
    columns = [
        'alternative',
        'effect_type',
        'effect_gene_types',
        'effect_gene_genes',
        'effect_details_transcript_ids',
        # 'effect_details_genes',
        'effect_details_details'
    ]
    df[columns] = df[columns].fillna('')

    df1 = effect_annotator.annotate_df(df)
    df2 = variant_effect_annotator.annotate_df(df)

    columns = [
        'VCF:chr',
        'VCF:position',
        'CSHL:location',
        'CSHL:variant',
        'effect_type',
        'effect_genes',
    ]
    print(df1[columns])
    print(df2[columns])
