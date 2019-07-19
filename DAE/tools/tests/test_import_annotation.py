import pandas as pd

from box import Box

from annotation.tools.file_io_parquet import ParquetReader

from backends.configure import Configure
from backends.vcf.raw_vcf import RawFamilyVariants
from backends.vcf.annotate_allele_frequencies import \
    VcfAlleleFrequencyAnnotator
from backends.impala.import_tools import variants_iterator_to_parquet

from .conftest import relative_to_this_test_folder


def test_annotation_pipeline(
        annotation_pipeline_vcf, vcf_variants_io, capsys, result_df):

    assert annotation_pipeline_vcf is not None

    captured = capsys.readouterr()
    with vcf_variants_io("thrift_import/effects_trio.vcf.gz") as io_manager:
        annotation_pipeline_vcf.annotate_file(io_manager)
    captured = capsys.readouterr()

    df = result_df(captured.out)
    print(df)

    pd.testing.assert_series_equal(
        df['score0'],
        df['POS']/1.0,
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


# FIXME:
# def test_variants_iterator_to_parquet(
#         annotation_pipeline_internal, temp_dirname):
#     vcf_prefix = relative_to_this_test_folder('thrift_import/effects_trio')
#     print(vcf_prefix)
#     vcf_config = Configure.from_prefix_vcf(vcf_prefix)

#     print(vcf_config)
#     freq_annotator = VcfAlleleFrequencyAnnotator()

#     fvars = RawFamilyVariants(vcf_config, annotator=freq_annotator)
#     assert fvars is not None

#     parquet_config = Configure.from_prefix_parquet(temp_dirname)

#     variants_iterator_to_parquet(
#         fvars,
#         temp_dirname,
#         annotation_pipeline=annotation_pipeline_internal,
#     )

#     parquet_summary = parquet_config.parquet.summary_variant
#     options = Box({
#         'infile': parquet_summary,
#     }, default_box=True, default_box_attr=None)

#     summary = ParquetReader(options)
#     summary._setup()
#     summary._cleanup()

#     # print(summary.schema)
#     schema = summary.schema
#     print(schema['score0'])

#     assert schema['score0'].type_name == 'float'
#     assert schema['score2'].type_name == 'float'
#     assert schema['score4'].type_name == 'float'

#     # print(schema['effect_gene_genes'])
#     assert schema['effect_gene_genes'].type_name == 'list(str)'
#     assert schema['effect_gene_types'].type_name == 'list(str)'
#     assert schema['effect_details_transcript_ids'].type_name == 'list(str)'
#     assert schema['effect_details_details'].type_name == 'list(str)'

#     assert schema['effect_genes'].type_name == 'list(str)'
#     assert schema['effect_details'].type_name == 'list(str)'
