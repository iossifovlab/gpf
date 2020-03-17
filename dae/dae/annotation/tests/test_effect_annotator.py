import pytest

import pandas as pd
import numpy as np


from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.annotation.tools.annotator_config import AnnotationConfigParser
from dae.annotation.tools.effect_annotator import (
    EffectAnnotator,
    VariantEffectAnnotator,
)

from dae.annotation.tests.conftest import relative_to_this_test_folder


@pytest.fixture(scope="session")
def effect_annotator(genomes_db_2013):
    options = GPFConfigParser._dict_to_namedtuple(
        {
            "vcf": True,
            "direct": False,
            "r": "reference",
            "a": "alternative",
            "c": "chrom",
            "p": "position",
            "prom_len": 0,
        }
    )

    columns = {
        "effect_type": "effect_type",
        "effect_gene": "effect_genes",
        "effect_details": "effect_details",
    }

    config = AnnotationConfigParser.parse_section(
        GPFConfigParser._dict_to_namedtuple(
            {
                "options": options,
                "columns": columns,
                "annotator": "effect_annotator.EffectAnnotator",
                "virtual_columns": [],
            }
        )
    )

    annotator = EffectAnnotator(config, genomes_db_2013)
    assert annotator is not None

    return annotator


@pytest.fixture(scope="session")
def variant_effect_annotator(genomes_db_2013):
    options = GPFConfigParser._dict_to_namedtuple(
        {
            "direct": False,
            "vcf": True,
            "r": "reference",
            "a": "alternative",
            "c": "chrom",
            "p": "position",
            "prom_len": 0,
        }
    )

    columns = {
        "effect_type": "effect_type",
        "effect_genes": "effect_genes",
        "effect_gene_genes": "effect_gene_genes",
        "effect_gene_types": "effect_gene_types",
        "effect_details": "effect_details",
        "effect_details_transcript_ids": "effect_details_transcript_ids",
        "effect_details_genes": "effect_details_genes",
        "effect_details_details": "effect_details_details",
    }

    config = AnnotationConfigParser.parse_section(
        GPFConfigParser._dict_to_namedtuple(
            {
                "options": options,
                "columns": columns,
                "annotator": "effect_annotator.VariantEffectAnnotator",
                "virtual_columns": [],
            }
        )
    )

    annotator = VariantEffectAnnotator(config, genomes_db_2013)
    assert annotator is not None

    return annotator


def test_effect_annotator(effect_annotator, variants_io, capsys):
    with variants_io("fixtures/effects_trio_multi-effect.txt") as io_manager:

        captured = capsys.readouterr()

        effect_annotator.annotate_file(io_manager)

    captured = capsys.readouterr()
    print(captured.err)
    print(captured.out)

    print(effect_annotator.schema)


def test_effect_annotator_df(variant_effect_annotator):
    df = pd.read_csv(
        relative_to_this_test_folder("fixtures/effects_trio_multi-effect.txt"),
        dtype={"chrom": str, "position": np.int32},
        sep="\t",
    )

    columns = [
        "alternative",
        "effect_type",
        "effect_gene_types",
        "effect_gene_genes",
        "effect_details_transcript_ids",
        # 'effect_details_genes',
        "effect_details_details",
    ]
    df[columns] = df[columns].fillna("")
    print(df[["effect_type", "effect_gene_types", "effect_gene_genes"]])

    res_df = variant_effect_annotator.annotate_df(df)
    print(res_df[["effect_type", "effect_gene_types", "effect_gene_genes"]])

    assert list(res_df.effect_type.values) == list(df["effect_type"].values)


def test_effect_annotators_compare(
    effect_annotator, variant_effect_annotator, variants_io, capsys
):
    assert effect_annotator is not None
    assert variant_effect_annotator is not None
    df = pd.read_csv(
        relative_to_this_test_folder("fixtures/effects_trio_multi-effect.txt"),
        dtype={"chrom": str, "position": np.int32},
        sep="\t",
    )
    columns = [
        "alternative",
        "effect_type",
        "effect_gene_types",
        "effect_gene_genes",
        "effect_details_transcript_ids",
        # 'effect_details_genes',
        "effect_details_details",
    ]
    df[columns] = df[columns].fillna("")

    df1 = effect_annotator.annotate_df(df)
    df2 = variant_effect_annotator.annotate_df(df)

    columns = [
        "VCF_chr",
        "VCF_position",
        "CSHL_location",
        "CSHL_variant",
        "effect_type",
        "effect_genes",
    ]
    print(df1[columns])
    print(df2[columns])
