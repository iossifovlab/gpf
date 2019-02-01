import pytest
import os

import pandas as pd

from box import Box

from configurable_entities.configuration import DAEConfig

from annotation.annotation_pipeline import PipelineAnnotator
from annotation.tools.file_io_parquet import ParquetReader

from backends.configure import Configure
from backends.vcf.raw_vcf import RawFamilyVariants
from backends.vcf.annotate_allele_frequencies import \
    VcfAlleleFrequencyAnnotator
from backends.thrift.import_tools import variants_iterator_to_parquet

from tools.vcf2parquet import parse_cli_arguments, import_vcf

from .conftest import relative_to_this_test_folder


@pytest.fixture(scope='session')
def annotation_pipeline():
    filename = relative_to_this_test_folder(
        "thrift_import/import_annotation.conf")

    options = Box({
            "default_arguments": None,
            "vcf": True,
            # "mode": "overwrite",
        },
        default_box=True,
        default_box_attr=None)

    pipeline = PipelineAnnotator.build(
        options, filename,
        defaults={
            "fixtures_dir": relative_to_this_test_folder("thrift_import/")
        })
    return pipeline


@pytest.fixture(scope='session')
def annotation_pipeline_df():
    filename = relative_to_this_test_folder(
        "thrift_import/import_annotation.conf")

    options = Box({
            "default_arguments": None,
            "vcf": True,
            'c': 'chrom',
            'p': 'position',
            'r': 'reference',
            'a': 'alternative',
            # "mode": "overwrite",
        },
        default_box=True,
        default_box_attr=None)

    pipeline = PipelineAnnotator.build(
        options, filename,
        defaults={
            "fixtures_dir": relative_to_this_test_folder("thrift_import/")
        })
    return pipeline


def test_annotation_pipeline(
        annotation_pipeline, vcf_variants_io, capsys, result_df):

    assert annotation_pipeline is not None

    captured = capsys.readouterr()
    with vcf_variants_io("thrift_import/effects_trio.vcf.gz") as io_manager:
        annotation_pipeline.annotate_file(io_manager)
    captured = capsys.readouterr()

    df = result_df(captured.out)
    print(df)

    pd.testing.assert_series_equal(
        df['score0'],
        df['POS'],
        check_less_precise=1,
        check_names=False,
    )
    pd.testing.assert_series_equal(
        df['score2'],
        df['POS']/100.0,
        check_less_precise=1,
        check_names=False,
    )
    pd.testing.assert_series_equal(
        df['score4'],
        df['POS']/10000.0,
        check_less_precise=1,
        check_names=False,
    )


def test_variants_iterator_to_parquet(annotation_pipeline_df, temp_dirname):
    vcf_prefix = relative_to_this_test_folder('thrift_import/effects_trio')
    print(vcf_prefix)
    vcf_config = Configure.from_prefix_vcf(vcf_prefix)

    print(vcf_config)
    freq_annotator = VcfAlleleFrequencyAnnotator()

    fvars = RawFamilyVariants(vcf_config, annotator=freq_annotator)
    assert fvars is not None

    parquet_prefix = os.path.join(temp_dirname, "effects_trio_")
    print(parquet_prefix)
    parquet_config = Configure.from_prefix_parquet(parquet_prefix)

    variants_iterator_to_parquet(
        fvars,
        parquet_prefix,
        annotation_pipeline=annotation_pipeline_df,
    )

    parquet_summary = parquet_config.parquet.summary_variant
    options = Box({
        'infile': parquet_summary,
    }, default_box=True, default_box_attr=None)

    summary = ParquetReader(options)
    summary._setup()
    summary._cleanup()

    # print(summary.schema)
    schema = summary.schema
    print(schema['score0'])

    assert schema['score0'].type_name == 'float'
    assert schema['score2'].type_name == 'float'
    assert schema['score4'].type_name == 'float'

    # print(schema['effect_gene_genes'])
    assert schema['effect_gene_genes'].type_name == 'list(str)'
    assert schema['effect_gene_types'].type_name == 'list(str)'
    assert schema['effect_details_transcript_ids'].type_name == 'list(str)'
    assert schema['effect_details_details'].type_name == 'list(str)'

    assert schema['effect_genes'].type_name == 'list(str)'
    assert schema['effect_details'].type_name == 'list(str)'


def test_vcf2parquet(temp_dirname):
    annotation_config = relative_to_this_test_folder(
        "thrift_import/import_annotation.conf")
    vcf_prefix = relative_to_this_test_folder('thrift_import/effects_trio')
    vcf_config = Configure.from_prefix_vcf(vcf_prefix)

    argv = [
        'vcf',
        '--annotation', annotation_config,
        '-o', temp_dirname,
        vcf_config.vcf.pedigree,
        vcf_config.vcf.vcf
    ]

    dae_config = DAEConfig()
    argv = parse_cli_arguments(dae_config, argv)
    assert argv.type == 'vcf'

    import_vcf(dae_config, argv, defaults={
            "fixtures_dir": relative_to_this_test_folder("thrift_import/")
    })

    parquet_summary = Configure.from_prefix_parquet(
        temp_dirname).parquet.summary_variant
    summary = ParquetReader(Box({
        'infile': parquet_summary,
    }, default_box=True, default_box_attr=None))
    summary._setup()
    summary._cleanup()

    # print(summary.schema)
    schema = summary.schema
    print(schema['score0'])

    assert schema['score0'].type_name == 'float'
    assert schema['score2'].type_name == 'float'
    assert schema['score4'].type_name == 'float'

    # print(schema['effect_gene_genes'])
    assert schema['effect_gene_genes'].type_name == 'list(str)'
    assert schema['effect_gene_types'].type_name == 'list(str)'
    assert schema['effect_details_transcript_ids'].type_name == 'list(str)'
    assert schema['effect_details_details'].type_name == 'list(str)'

    assert schema['effect_genes'].type_name == 'list(str)'
    assert schema['effect_details'].type_name == 'list(str)'
