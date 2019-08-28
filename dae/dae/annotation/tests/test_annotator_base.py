import pytest
import pandas as pd

from .conftest import relative_to_this_test_folder
from box import Box
from dae.annotation.tools.annotator_base import AnnotatorBase, \
    CopyAnnotator
from dae.annotation.tools.annotator_config import VariantAnnotatorConfig

from dae.annotation.tools.file_io import IOManager, IOType


@pytest.fixture
def variants_io1(request):
    io_config = {
        "infile": relative_to_this_test_folder("fixtures/input.tsv"),
        "outfile": "-",
    }
    io_config = Box(io_config, default_box=True, default_box_attr=None)
    io_manager = IOManager(io_config, IOType.TSV, IOType.TSV)
    return io_manager


@pytest.fixture
def variants_io_m(request):
    io_config = {
        "infile": relative_to_this_test_folder("fixtures/input_multi.tsv"),
        "outfile": "-",
    }
    io_config = Box(io_config, default_box=True, default_box_attr=None)
    io_manager = IOManager(io_config, IOType.TSV, IOType.TSV)
    return io_manager


def test_create_file_io():
    io = {
        "infile": relative_to_this_test_folder("fixtures/input.tsv"),
        "outfile": "-",
    }
    io_config = Box(io, default_box=True, default_box_attr=None)
    with IOManager(io_config, IOType.TSV, IOType.TSV) as io:
        assert io is not None
        lines = list(io.lines_read_iterator())
        print(lines)
        assert len(lines) == 4
        print(io.header)
        assert len(io.header) == 3


def test_annotator_base_simple():
    opts = Box({}, default_box=True, default_box_attr=None)

    section_config = VariantAnnotatorConfig(
        name="base",
        annotator_name="annotator_base.AnnotatorBase",
        options=opts,
        columns_config={
            "CSHL:chr": "chr",
            "CSHL:position": "pos"
        },
        virtuals=[]
    )

    annotator = AnnotatorBase(section_config)
    assert annotator is not None


def test_copy_annotator_simple(capsys, variants_io1):
    opts = Box({}, default_box=True, default_box_attr=None)

    section_config = VariantAnnotatorConfig(
        name="copy",
        annotator_name="annotator_base.CopyAnnotator",
        options=opts,
        columns_config={
            "location": "loc1",
            "variant": "var1"
        },
        virtuals=[]
    )

    with variants_io1 as io_manager:
        annotator = CopyAnnotator(section_config)
        assert annotator is not None
        capsys.readouterr()
        annotator.annotate_file(io_manager)

    # print(variants_input.output)
    captured = capsys.readouterr()

    print(captured.out)
    print(captured.err)
    # assert captured.err == "Processed 4 lines.\n"


def test_copy_annotator_multi(capsys, variants_io_m, expected_df):
    opts = Box({}, default_box=True, default_box_attr=None)

    section_config = VariantAnnotatorConfig(
        name="copy",
        annotator_name="annotator_base.CopyAnnotator",
        options=opts,
        columns_config={
            "location": "loc1",
            "variant": "var1"
        },
        virtuals=[]
    )

    df = pd.read_csv(
        relative_to_this_test_folder("fixtures/input_multi.tsv"),
        sep='\t')
    print(df)

    print(df[['test1', 'test2']])

    with variants_io_m as io_manager:
        annotator = CopyAnnotator(section_config)
        assert annotator is not None
        capsys.readouterr()
        annotator.annotate_file(io_manager)

    # print(variants_input.output)
    captured = capsys.readouterr()

    print(captured.out)
    print(captured.err)
    res_df = expected_df(captured.out)
    print(res_df)
    print(res_df[['test1', 'test2']])

    pd.testing.assert_frame_equal(
        df[['test1', 'test2']],
        res_df[['test1', 'test2']]
    )
