from __future__ import print_function, absolute_import

import pytest

import pandas as pd
import numpy as np

from box import Box

from annotation.tools.annotator_config import VariantAnnotatorConfig
from annotation.tools.effect_annotator import EffectAnnotator

from .conftest import relative_to_this_test_folder


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
        'effect_type': 'effectType',
        'effect_gene': 'effectGene',
        'effect_details': 'effectDetails'
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


def test_effect_annotator(effect_annotator, variants_io, capsys):
    with variants_io("fixtures/effects_trio_multi-eff.txt") as io_manager:

        captured = capsys.readouterr()

        effect_annotator.annotate_file(io_manager)

    captured = capsys.readouterr()
    print(captured.err)
    print(captured.out)


def test_effect_annotator_df(effect_annotator):
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
        'effect_details_details'
    ]
    df[columns] = df[columns].fillna('')
    print(df)

    res_df = effect_annotator.annotate_df(df)
    print(res_df)

