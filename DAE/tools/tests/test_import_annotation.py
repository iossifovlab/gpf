import pandas as pd

from box import Box

from annotation.annotation_pipeline import PipelineAnnotator

from .conftest import relative_to_this_test_folder


def test_annotation_pipeline(vcf_variants_io, capsys, result_df):
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
    assert pipeline is not None

    captured = capsys.readouterr()
    with vcf_variants_io("thrift_import/effects_trio.vcf.gz") as io_manager:
        pipeline.annotate_file(io_manager)
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
    