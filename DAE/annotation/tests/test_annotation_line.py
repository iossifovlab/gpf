import os
import pytest
from box import Box
import common.config
import annotation
from annotation.annotation_pipeline import MyConfigParser
from annotation.tools.annotator_base import AnnotationConfig, \
    AnnotationSection


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        path
    )


def test_annotation_line_simple():
    config_parser = MyConfigParser()
    config_parser.optionxform = str
    filename = relative_to_this_test_folder(
        "fixtures/multi_score_annotator.conf")
    config_parser.read(filename)
    config = Box(
        common.config.to_dict(config_parser),
        default_box=True, default_box_attr=None)
    assert config is not None
    print(config)

    print(config.keys())
    print(config_parser.sections())


@pytest.mark.parametrize('data,expected', [
    ("direct:True", {"direct": True}),
    ("default:False,direct:True", {"direct": True, "default": False}),
])
def test_parse_default_options(data, expected):
    result = AnnotationConfig._parse_default_options(data)
    assert result == expected


def test_parse_annotation_config():
    filename = relative_to_this_test_folder(
        "fixtures/annotation_test.conf")
    configuration = AnnotationConfig._parse_annotation_config(filename)
    print(configuration)

    assert len(list(configuration.keys())) == 5
    assert list(configuration.keys()) == [
        "Step1", "Step2", "Step3", "Step4", "Step5", ]


@pytest.fixture
def error_annotation_sections_configuration():
    filename = relative_to_this_test_folder(
        "fixtures/error_annotation_sections.conf")
    configuration = AnnotationConfig._parse_annotation_config(filename)

    return configuration


@pytest.fixture
def annotation_sections_configuration():
    filename = relative_to_this_test_folder(
        "fixtures/annotation_test.conf")
    configuration = AnnotationConfig._parse_annotation_config(filename)

    assert len(list(configuration.keys())) == 5
    assert list(configuration.keys()) == [
        "Step1", "Step2", "Step3", "Step4", "Step5"]
    return configuration


def test_parse_error_annotation_section_missing_annotator(
        error_annotation_sections_configuration):
    error_configuration = error_annotation_sections_configuration
    annotation_config = AnnotationConfig()

    with pytest.raises(AssertionError):
        annotation_config._parse_annotation_section(
            "Step0",
            error_configuration["Step0"])


def test_parse_annotation_section_sections(
        annotation_sections_configuration):
    configuration = annotation_sections_configuration
    annotation_config = AnnotationConfig()

    section1 = annotation_config._parse_annotation_section(
        "Step1", configuration["Step1"])
    assert section1.name == "Step1"

    section3 = annotation_config._parse_annotation_section(
        "Step3", configuration["Step3"])
    assert section3.name == "Step3"


def test_build_annotation_configuration():
    args = Box({
        "default_arguments": None,
        }, 
        default_box=True, 
        default_box_attr=None)

    header = ["#chr", "position", "ref", "alt"]
    filename = relative_to_this_test_folder(
        "fixtures/annotation_test.conf")

    config = AnnotationConfig.build(
        args, filename, header)
    assert config is not None

    for section in config.annotation_sections:
        print(section.name, "->", section.output_columns)

    assert config.output_length() == 21
    assert config.default_options.region is None


def test_build_annotation_configuration_region(annotation_test_conf):
    assert annotation_test_conf.default_options.region == "1:100001-1000001"


@pytest.fixture
def annotation_test_conf():
    args = Box({
        "region": "1:100001-1000001",
        },
        default_box=True, 
        default_box_attr=None)

    header = ["#chr", "position", "ref", "alt"]
    filename = relative_to_this_test_folder(
        "fixtures/annotation_test.conf")

    config = AnnotationConfig.build(
        args, filename, header)
    return config


def test_build_annotation_configuration_step5(annotation_test_conf):
    section = annotation_test_conf.annotation_sections[5]
    assert section.name == "Step5"

    print(section.options)
    assert section.options['c'] == "VCF:chr"
    assert section.options['p'] == "VCF:position"
    assert not section.options['gzip']


def test_build_annotation_configuration_step2(annotation_test_conf):
    section = annotation_test_conf.annotation_sections[2]
    assert section.name == "Step2"

    print(section.options)
    assert section.options['c'] == "CSHL:chr"
    assert section.options['p'] == "CSHL:position"

    assert len(section.native_columns) == 4
    assert len(section.input_columns) == 4
    assert len(section.output_columns) == 2
    assert len(section.virtual_columns) == 2


def test_annotator_class_instance():
    clazz = AnnotationSection._name_to_class(
        "annotation.tools.relabel_chromosome.RelabelChromosomeAnnotator"
    )
    assert clazz is not None
    assert clazz == \
        annotation.tools.relabel_chromosome.RelabelChromosomeAnnotator

    clazz = AnnotationSection._name_to_class(
        "annotate_with_multiple_scores.MultipleScoresAnnotator"
    )
    assert clazz is not None
    assert clazz == \
        annotation.tools.annotate_with_multiple_scores.MultipleScoresAnnotator
