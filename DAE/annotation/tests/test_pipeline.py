from __future__ import unicode_literals
from __future__ import print_function

import pytest
import pandas as pd

from box import Box

from annotation.annotation_pipeline import PipelineConfig, PipelineAnnotator

from .utils import relative_to_this_test_folder


# @pytest.mark.parametrize('data,expected', [
#     ("direct:True", {"direct": True}),
#     ("default:False,direct:True", {"direct": True, "default": False}),
# ])
# def test_parse_default_options(data, expected):
#     result = PipelineConfig._parse_default_options(data)
#     assert result == expected

@pytest.fixture
def empty_options():
    return Box({"vcf": True}, default_box=True, default_box_attr=None)


def test_parse_pipeline_config():
    filename = relative_to_this_test_folder(
        "fixtures/annotation_test.conf")
    configuration = PipelineConfig._parse_pipeline_config(filename)
    print(configuration)

    assert len(list(configuration.keys())) == 5
    assert list(configuration.keys()) == [
        "Step1", "Step2", "Step3", "Step4", "Step5", ]


@pytest.fixture
def error_pipeline_sections_configuration():
    filename = relative_to_this_test_folder(
        "fixtures/error_annotation_sections.conf")
    configuration = PipelineConfig._parse_pipeline_config(filename)

    return configuration


@pytest.fixture
def pipeline_sections_configuration():
    filename = relative_to_this_test_folder(
        "fixtures/annotation_test.conf")
    configuration = PipelineConfig._parse_pipeline_config(filename)

    assert len(list(configuration.keys())) == 5
    assert list(configuration.keys()) == [
        "Step1", "Step2", "Step3", "Step4", "Step5"]
    return configuration


def test_parse_error_pipeline_section_missing_annotator(
        error_pipeline_sections_configuration, empty_options):
    error_configuration = error_pipeline_sections_configuration

    with pytest.raises(AssertionError):
        PipelineConfig._parse_config_section(
            "Step0",
            error_configuration["Step0"],
            empty_options)


def test_parse_annotation_section_sections(
        pipeline_sections_configuration, empty_options):
    configuration = pipeline_sections_configuration

    section1 = PipelineConfig._parse_config_section(
        "Step1", configuration["Step1"], empty_options)
    assert section1.name == "Step1"

    section3 = PipelineConfig._parse_config_section(
        "Step3", configuration["Step3"], empty_options)
    assert section3.name == "Step3"


def test_build_pipeline_configuration():
    options = Box({
            "default_arguments": None,
            "vcf": True,
        }, 
        default_box=True, 
        default_box_attr=None)

    filename = relative_to_this_test_folder(
        "fixtures/annotation_test.conf")

    config = PipelineConfig.build(
        options, filename)
    assert config is not None

    for section in config.pipeline_sections:
        print(section.name, "->", section.output_columns)

    # assert config.output_length() == 21
    # assert config.default_options.region is None


input2_copy_expected = """loc1\tvar1
1:10918\tsub(G->A)
1:10919\tsub(A->C)
1:10920\tsub(G->T)
1:10921\tsub(A->C)
1:10922\tsub(G->C)
"""

input2_score_expected = """loc1\tvar1\tRESULT_phastCons100way
1:10918\tsub(G->A)\t-100
1:10919\tsub(A->C)\t0.251
1:10920\tsub(G->T)\t0.249
1:10921\tsub(A->C)\t0.247
1:10922\tsub(G->C)\t0.245
"""

input2_score2_expected = \
    """loc1\tvar1\tRESULT_phastCons100way\tRESULT_RawScore\tRESULT_PHRED
1:10918\tsub(G->A)\t-100\t0.40161\t6.631
1:10919\tsub(A->C)\t0.251\t0.537788\t7.986
1:10920\tsub(G->T)\t0.249\t0.371362\t6.298
1:10921\tsub(A->C)\t0.247\t0.537794\t7.986
1:10922\tsub(G->C)\t0.245\t0.391539\t6.522
"""


@pytest.mark.parametrize("config_file,expected", [
    ("fixtures/copy_annotator.conf", input2_copy_expected),
    ("fixtures/score_annotator.conf", input2_score_expected),
    # ("fixtures/score2_annotator.conf", input2_score2_expected),
])
def test_build_pipeline(
        expected_df, variants_io, capsys, config_file, expected):
    
    options = Box({
            "default_arguments": None,
            "vcf": True,
        },
        default_box=True,
        default_box_attr=None)

    filename = relative_to_this_test_folder(config_file)

    pipeline = PipelineAnnotator.build(
        options, filename, defaults={
            "fixtures_dir": relative_to_this_test_folder("fixtures/")
        })
    assert pipeline is not None

    captured = capsys.readouterr()
    with variants_io("fixtures/input2.tsv") as io_manager:
        pipeline.annotate_file(io_manager)
    captured = capsys.readouterr()

    print(captured.err)
    print(captured.out)

    cap_df = expected_df(captured.out)
    
    pd.testing.assert_frame_equal(
        cap_df, expected_df(expected),
        check_less_precise=3,
        check_names=False)


# def test_build_annotation_configuration_region(annotation_test_conf):
#     assert annotation_test_conf.default_options.region == "1:100001-1000001"


# @pytest.fixture
# def annotation_test_conf():
#     args = Box({
#         "region": "1:100001-1000001",
#         },
#         default_box=True, 
#         default_box_attr=None)

#     header = ["#chr", "position", "ref", "alt"]
#     filename = relative_to_this_test_folder(
#         "fixtures/annotation_test.conf")

#     config = AnnotationConfig.build(
#         args, filename, header)
#     return config


# def test_build_annotation_configuration_step5(annotation_test_conf):
#     section = annotation_test_conf.annotation_sections[5]
#     assert section.name == "Step5"

#     print(section.options)
#     assert section.options['c'] == "VCF:chr"
#     assert section.options['p'] == "VCF:position"
#     assert not section.options['gzip']


# def test_build_annotation_configuration_step2(annotation_test_conf):
#     section = annotation_test_conf.annotation_sections[2]
#     assert section.name == "Step2"

#     print(section.options)
#     assert section.options['c'] == "CSHL:chr"
#     assert section.options['p'] == "CSHL:position"

#     assert len(section.native_columns) == 4
#     assert len(section.input_columns) == 4
#     assert len(section.output_columns) == 2
#     assert len(section.virtual_columns) == 2


# def test_annotator_class_instance():
#     clazz = AnnotationSection._name_to_class(
#         "annotation.tools.relabel_chromosome.RelabelChromosomeAnnotator"
#     )
#     assert clazz is not None
#     assert clazz == \
#         annotation.tools.relabel_chromosome.RelabelChromosomeAnnotator

#     clazz = AnnotationSection._name_to_class(
#         "annotate_with_multiple_scores.MultipleScoresAnnotator"
#     )
#     assert clazz is not None
#     assert clazz == \
#         annotation.tools.annotate_with_multiple_scores.MultipleScoresAnnotator
