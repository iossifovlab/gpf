import pandas as pd


# def test_annotation_pipeline(
#         annotation_pipeline_vcf, vcf_variants_io, capsys, result_df):

#     assert annotation_pipeline_vcf is not None

#     captured = capsys.readouterr()
#     with vcf_variants_io("thrift_import/effects_trio.vcf.gz") as io_manager:
#         annotation_pipeline_vcf.annotate_file(io_manager)
#     captured = capsys.readouterr()

#     df = result_df(captured.out)
#     print(df)

#     pd.testing.assert_series_equal(
#         df["score0"], df["POS"] / 1.0, 
#         rtol=10e-1, check_names=False,
#     )
#     pd.testing.assert_series_equal(
#         df["score2"],
#         df["POS"] / 100.0,
#         rtol=10e-1,
#         check_names=False,
#     )
#     pd.testing.assert_series_equal(
#         df["score4"],
#         df["POS"] / 10000.0,
#         rtol=10e-1,
#         check_names=False,
#     )
