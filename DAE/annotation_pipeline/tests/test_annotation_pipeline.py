import pytest
from copy import deepcopy
from StringIO import StringIO

from annotation_pipeline.annotation_pipeline import MultiAnnotator,\
    MyConfigParser, str_to_class
from annotation_pipeline.tools.duplicate_columns import\
    DuplicateColumnsAnnotator
from annotation_pipeline.tests import configs
from annotation_pipeline.tests import input_output


class Annotator(object):

    def __init__(self, options, header):
        self.default = options['default']

    def line_annotations(self, line, new_columns):
        if self.default:
            return [line[1][:-3]]
        else:
            result = []
            for c in new_columns:
                if c == 'location':
                    result.append(line[1][:-1])
                elif c == 'variant':
                    result.append(line[2])
            return result


class Preannotator(object):

    def __init__(self):
        pass

    @property
    def new_columns(self):
        return ['TEST:location']

    def line_annotations(self, line, new_columns):
        return [line[1][:-2]]


@pytest.fixture
def mocker(mocker):
    mocker.patch.object(MyConfigParser, 'read', MyConfigParser.readfp)
    mocker.patch('annotation_pipeline.annotation_pipeline.str_to_class',
                 return_value=Annotator)


@pytest.fixture
def base_config():
    return StringIO(deepcopy(configs.BASE_CONFIG))


@pytest.fixture
def reannotate_config():
    return StringIO(deepcopy(configs.REANNOTATE_CONFIG))


@pytest.fixture
def defaults_arguments_config():
    return StringIO(deepcopy(configs.DEFAULT_ARGUMENTS_CONFIG))


@pytest.fixture
def virtuals_config():
    return StringIO(deepcopy(configs.VIRTUALS_CONFIG))


@pytest.fixture
def base_multi_annotator(base_config, mocker):
    return MultiAnnotator(base_config, header=['id', 'location', 'variant'])


@pytest.fixture
def reannotate_multi_annotator(reannotate_config, mocker):
    return\
        MultiAnnotator(reannotate_config, header=['id', 'location', 'variant'],
                       reannotate=True)


@pytest.fixture
def preannotator_multi_annotator(base_config, mocker):
    return MultiAnnotator(base_config, header=['id', 'location', 'variant'],
                          preannotators=[Preannotator()])


@pytest.fixture
def defaults_arguments_multi_annotator(defaults_arguments_config,
                                       reannotate_config, mocker):
    defaults_arguments_in_config =\
        MultiAnnotator(defaults_arguments_config,
                       header=['id', 'location', 'variant'],
                       default_arguments={'default': False})
    default_arguments_not_in_config =\
        MultiAnnotator(reannotate_config, header=['id', 'location', 'variant'],
                       default_arguments={'default': True})
    return [defaults_arguments_in_config, default_arguments_not_in_config]


@pytest.fixture
def virtuals_multi_annotator(virtuals_config, mocker):
    return\
        MultiAnnotator(virtuals_config, header=['id', 'location', 'variant'])


@pytest.fixture
def split_column_multi_annotator(base_config, mocker):
    return MultiAnnotator(base_config, header=['id', 'location', 'variant'],
                          split_column='location', split_separator='|')


@pytest.fixture
def base_input(mocker):
    return deepcopy(input_output.BASE_INPUT)


@pytest.fixture
def split_column_input(mocker):
    return deepcopy(input_output.SPLIT_COLUMN_INPUT)


@pytest.fixture
def multiple_headers_input(mocker):
    return deepcopy(input_output.MULTIPLE_HEADERS_INPUT)


@pytest.fixture
def base_output(mocker):
    return deepcopy(input_output.BASE_OUTPUT)


@pytest.fixture
def reannotate_output(mocker):
    return deepcopy(input_output.REANNOTATE_OUTPUT)


@pytest.fixture
def default_arguments_output(mocker):
    return deepcopy(input_output.DEFAULT_ARGUMENTS_OUTPUT)


@pytest.fixture
def split_column_output(mocker):
    return deepcopy(input_output.SPLIT_COLUMN_OUTPUT)


@pytest.fixture
def multiple_headers_output(mocker):
    return deepcopy(input_output.MULTIPLE_HEADERS_OUTPUT)


def test_str_to_class(mocker):
    assert str_to_class('duplicate_columns.DuplicateColumnsAnnotator') ==\
        DuplicateColumnsAnnotator


def test_base_config(base_multi_annotator, base_input, base_output, mocker):
    annotation_output = StringIO()
    base_multi_annotator.annotate_file(base_input, annotation_output)

    assert str(annotation_output.getvalue()) == str(base_output)

    annotation_output.close()


def test_reannotate(reannotate_multi_annotator, base_input,
                    reannotate_output, mocker):
    annotation_output = StringIO()
    reannotate_multi_annotator.annotate_file(base_input, annotation_output)

    assert str(annotation_output.getvalue()) == str(reannotate_output)

    annotation_output.close()


def test_preannotator(preannotator_multi_annotator, base_input,
                      base_output, mocker):
    annotation_output = StringIO()
    preannotator_multi_annotator.annotate_file(base_input, annotation_output)

    assert str(annotation_output.getvalue()) == str(base_output)

    annotation_output.close()


def test_default_arguments(defaults_arguments_multi_annotator, base_input,
                           default_arguments_output, mocker):
    annotation_output = StringIO()
    annotation_output_base = StringIO()
    defaults_arguments_multi_annotator[0]\
        .annotate_file(base_input, annotation_output)
    defaults_arguments_multi_annotator[1]\
        .annotate_file(base_input, annotation_output_base)

    assert str(annotation_output.getvalue()) == str(default_arguments_output)
    assert str(annotation_output_base.getvalue()) ==\
        str(default_arguments_output)

    annotation_output.close()


def test_virtuals(virtuals_multi_annotator, base_input, base_output, mocker):
    annotation_output = StringIO()
    virtuals_multi_annotator.annotate_file(base_input, annotation_output)

    assert str(annotation_output.getvalue()) == str(base_output)

    annotation_output.close()


def test_split_columns(split_column_multi_annotator, split_column_input,
                       split_column_output, mocker):
    annotation_output = StringIO()
    split_column_multi_annotator\
        .annotate_file(split_column_input, annotation_output)

    assert str(annotation_output.getvalue()) == str(split_column_output)

    annotation_output.close()


def test_multiple_headers(split_column_multi_annotator, multiple_headers_input,
                          multiple_headers_output, mocker):
    annotation_output = StringIO()
    split_column_multi_annotator\
        .annotate_file(multiple_headers_input, annotation_output)

    assert str(annotation_output.getvalue()) == str(multiple_headers_output)

    annotation_output.close()
