import pytest
from copy import deepcopy
from StringIO import StringIO

from annotation.annotation_pipeline import MultiAnnotator,\
    MyConfigParser, str_to_class
from annotation.tools.duplicate_columns import\
    DuplicateColumnsAnnotator
from annotation.tests import configs
from annotation.tests import input_output


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
    mocker.patch('annotation.annotation_pipeline.str_to_class',
                 return_value=Annotator)
    mocker.patch('annotation.annotation_pipeline.PreannotatorLoader.load_preannotators',
                 return_value=[Preannotator()])
    mocker.patch('annotation.annotation_pipeline.exists',
                 return_value=True)


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
def get_opts(config, reannotate=False, split=None, split_separator=']',
             skip_preannotators=True, default_args='default:False'):
    class AnnotatorOpts:
        def __init__(self, opt_conf, opt_reannotate, opt_split,
                     opt_splitsep, opt_skip_pre, opt_def_arg):
            self.config = opt_conf
            self.reannotate = opt_reannotate
            self.split = opt_split
            self.separator = opt_splitsep
            self.skip_preannotators = opt_skip_pre
            self.default_arguments = [opt_def_arg]
    return AnnotatorOpts(config, reannotate, split, split_separator,
                         skip_preannotators, default_args)


@pytest.fixture
def base_multi_annotator(base_config, mocker):
    base_opts = get_opts(base_config)
    return MultiAnnotator(base_opts, header=['id', 'location', 'variant'])


@pytest.fixture
def reannotate_multi_annotator(reannotate_config, mocker):
    reannotate_opts = get_opts(reannotate_config, reannotate=True)
    return MultiAnnotator(reannotate_opts, header=['id', 'location', 'variant'])


@pytest.fixture
def preannotator_multi_annotator(base_config, mocker):
    preannotator_opts = get_opts(base_config, skip_preannotators=False)
    return MultiAnnotator(preannotator_opts, header=['id', 'location', 'variant'])


@pytest.fixture
def defaults_arguments_multi_annotator(defaults_arguments_config, reannotate_config, mocker):
    defaults_arguments_opts = get_opts(defaults_arguments_config)
    defaults_arguments_opts_alt = get_opts(reannotate_config, default_args='default:True')
    return (MultiAnnotator(defaults_arguments_opts, header=['id', 'location', 'variant']),
            MultiAnnotator(defaults_arguments_opts_alt, header=['id', 'location', 'variant']))


@pytest.fixture
def virtuals_multi_annotator(virtuals_config, mocker):
    virtuals_opts = get_opts(virtuals_config)
    return MultiAnnotator(virtuals_opts, header=['id', 'location', 'variant'])


@pytest.fixture
def split_column_multi_annotator(base_config, mocker):
    split_column_opts = get_opts(base_config, split='location', split_separator='|')
    return MultiAnnotator(split_column_opts, header=['id', 'location', 'variant'])


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
    annotation_output_alt = StringIO()
    defaults_arguments_multi_annotator[0].annotate_file(base_input, annotation_output)
    assert str(annotation_output.getvalue()) == str(default_arguments_output)
    defaults_arguments_multi_annotator[1].annotate_file(base_input, annotation_output_alt)
    assert str(annotation_output_alt.getvalue()) == str(default_arguments_output)

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
