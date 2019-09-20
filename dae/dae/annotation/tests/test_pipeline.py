import pytest
import pandas as pd

from box import Box

from dae.annotation.annotation_pipeline import PipelineAnnotator
from dae.annotation.tools.annotator_config import AnnotationConfigParser
from dae.annotation.tools.annotator_base import VariantAnnotatorBase

from .conftest import relative_to_this_test_folder


@pytest.fixture
def empty_options():
    return Box({'vcf': True}, default_box=True, default_box_attr=None)


def test_parse_pipeline_config(genomes_db):
    filename = relative_to_this_test_folder('fixtures/annotation_test.conf')
    work_dir = relative_to_this_test_folder('fixtures')
    configuration = AnnotationConfigParser.read_file_configuration(
        filename, work_dir
    )

    assert len(list(configuration.keys())) == 6
    assert list(configuration.keys()) == [
        'Step1', 'Step2', 'Step3', 'Step4', 'Step5', 'config_file']


@pytest.fixture
def error_pipeline_sections_configuration(genomes_db):
    filename = relative_to_this_test_folder(
        'fixtures/error_annotation_sections.conf')
    work_dir = relative_to_this_test_folder('fixtures')
    configuration = AnnotationConfigParser.read_file_configuration(
        filename, work_dir
    )

    return configuration


@pytest.fixture
def pipeline_sections_configuration(genomes_db):
    filename = relative_to_this_test_folder(
        'fixtures/annotation_test.conf')
    work_dir = relative_to_this_test_folder('fixtures')
    configuration = AnnotationConfigParser.read_file_configuration(
        filename, work_dir
    )

    assert len(list(configuration.keys())) == 6
    assert list(configuration.keys()) == [
        'Step1', 'Step2', 'Step3', 'Step4', 'Step5', 'config_file']
    return configuration


def test_parse_error_pipeline_section_missing_annotator(
        error_pipeline_sections_configuration, empty_options, genomes_db):
    error_configuration = error_pipeline_sections_configuration
    configuration = error_configuration['Step0']
    configuration['options'] = empty_options

    with pytest.raises(AssertionError):
        AnnotationConfigParser.parse_section(configuration, genomes_db)


def test_parse_annotation_section_sections(
        pipeline_sections_configuration, empty_options, genomes_db):
    configuration = pipeline_sections_configuration

    step1_configuration = configuration['Step1']
    step1_configuration['options'] = empty_options

    section1 = \
        AnnotationConfigParser.parse_section(step1_configuration, genomes_db)
    assert section1.annotator == \
        'relabel_chromosome.RelabelChromosomeAnnotator'

    step3_configuration = configuration['Step3']
    step3_configuration['options'] = empty_options

    section3 = \
        AnnotationConfigParser.parse_section(step3_configuration, genomes_db)
    assert section3.annotator == 'annotator_base.CopyAnnotator'


def test_build_pipeline_configuration(genomes_db):
    options = Box({
            'default_arguments': None,
            'vcf': True,
            'mode': 'overwrite',
        },
        default_box=True,
        default_box_attr=None)

    filename = relative_to_this_test_folder('fixtures/annotation_test.conf')
    work_dir = relative_to_this_test_folder('fixtures')

    config = AnnotationConfigParser.read_and_parse_file_configuration(
        options, filename, work_dir, genomes_db
    )
    assert config is not None

    for section in config.sections:
        print(section.annotator, '->', section.output_columns)

    # assert config.output_length() == 21
    # assert config.default_options.region is None


input2_copy_expected = '''chr\tposition
1\t10918
1\t10919
1\t10920
1\t10921
1\t10922
'''

input2_score_expected = '''RESULT_phastCons100way\tloc1\tvar1
0.253\t1:10918\tsub(G->A)
0.251\t1:10919\tsub(A->C)
0.249\t1:10920\tsub(G->T)
0.247\t1:10921\tsub(A->C)
0.245\t1:10922\tsub(G->C)
'''

input2_score2_expected = \
    '''loc1\tvar1\tRESULT_phastCons100way\tRESULT_RawScore\tRESULT_PHRED
1:10918\tsub(G->A)\t0.253\t0.40161\t6.631
1:10919\tsub(A->C)\t0.251\t0.537788\t7.986
1:10920\tsub(G->T)\t0.249\t0.371362\t6.298
1:10921\tsub(A->C)\t0.247\t0.537794\t7.986
1:10922\tsub(G->C)\t0.245\t0.391539\t6.522
'''


@pytest.mark.parametrize('config_file,expected', [
    ('fixtures/copy_annotator.conf', input2_copy_expected),
    ('fixtures/score_annotator.conf', input2_score_expected),
    ('fixtures/score2_annotator.conf', input2_score2_expected),
])
def test_build_pipeline(
        expected_df, variants_io, capsys, config_file, expected, genomes_db):

    options = Box({
            'default_arguments': None,
            'vcf': True,
            'mode': 'overwrite',
        },
        default_box=True,
        default_box_attr=None)

    filename = relative_to_this_test_folder(config_file)

    captured = capsys.readouterr()
    with variants_io('fixtures/input2.tsv') as io_manager:
        work_dir = relative_to_this_test_folder('fixtures/')
        pipeline = PipelineAnnotator.build(
            options, filename, work_dir, genomes_db,
            defaults={'values': {'fixtures_dir': work_dir}}
        )
        assert pipeline is not None
        pipeline.annotate_file(io_manager)
    captured = capsys.readouterr()

    print(captured.err)
    print(captured.out)

    cap_df = expected_df(captured.out)

    pd.testing.assert_frame_equal(
        cap_df, expected_df(expected),
        check_less_precise=3,
        check_names=False)


def dummy_variant_annotate(annotator, aline, variant):
    # print(variant)

    aline['changed_chrom'] = 'test'
    aline['changed_position'] = 42


@pytest.fixture(autouse=True)
def mock(mocker):
    mocker.patch.object(
        VariantAnnotatorBase, 'do_annotate', new=dummy_variant_annotate)


expected_change_variants_position = \
    '''test_copy_chr	test_copy_pos	test_vcf_chr	''' \
    '''test_vcf_pos	test_cshl_chr	test_cshl_pos
test	42	test	42	test	42
test	42	test	42	test	42
test	42	test	42	test	42
test	42	test	42	test	42
test	42	test	42	test	42
'''


def test_pipeline_change_variants_position(
        variants_io, capsys, expected_df, genomes_db):

    options = Box({
            'default_arguments': None,
            'vcf': True,
            'mode': 'overwrite',
        },
        default_box=True,
        default_box_attr=None)

    filename = relative_to_this_test_folder(
        'fixtures/variant_coordinates_change.conf')

    with variants_io('fixtures/input2.tsv') as io_manager:
        work_dir = relative_to_this_test_folder('fixtures/')
        pipeline = PipelineAnnotator.build(
            options, filename, work_dir, genomes_db,
            defaults={'values': {'fixtures_dir': work_dir}}
        )
        assert pipeline is not None

        pipeline.annotate_file(io_manager)
    captured = capsys.readouterr()

    print(captured.err)
    print(captured.out)

    pd.testing.assert_frame_equal(
        expected_df(captured.out),
        expected_df(expected_change_variants_position),
        check_less_precise=3,
        check_names=False)
