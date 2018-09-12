import pytest
from copy import deepcopy
from StringIO import StringIO
from box import Box

from annotation.annotation_pipeline import MultiAnnotator,\
    MyConfigParser, str_to_class
from annotation.tools.duplicate_columns import\
    DuplicateColumnsAnnotator
from annotation.tests import configs
from annotation.tests import input_output
from annotation.tools import file_io


class Annotator(object):

    def __init__(self, options, header):
        self.default = options.default

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


def mocked_open(fileinp, mode):
    return fileinp


@pytest.fixture
def mocker(mocker):
    mocker.patch.object(MyConfigParser, 'read', MyConfigParser.readfp)
    mocker.patch('annotation.annotation_pipeline.str_to_class',
                 return_value=Annotator)
    mocker.patch('annotation.annotation_pipeline.PreannotatorLoader.load_preannotators',
                 return_value=[Preannotator()])
    mocker.patch('annotation.annotation_pipeline.exists',
                 return_value=True)
    mocker.patch.object(file_io, 'open', mocked_open)
    mocker.patch('annotation.tools.file_io.assert_file_exists', return_value=True)
    mocker.patch('os.path.getsize', return_value=1)


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
def get_opts(infile, outfile, config, append=True,
             split=None, split_separator=']',
             skip_preannotators=True, default_args='default:False'):
    options = {
        'infile': infile,
        'outfile': outfile,
        'config': config,
        'append': append,
        'split': split,
        'separator': split_separator,
        'skip_preannotators': skip_preannotators,
        'default_arguments': default_args.split(','),
        'no_header': True,
        'region': None,
    }
    return Box(options, default_box=True, default_box_attr=None)


@pytest.fixture
def base_opts(base_input, base_config, mocker):
    return get_opts(base_input, StringIO(), base_config)


@pytest.fixture
def reannotate_opts(base_input, reannotate_config, mocker):
    return get_opts(base_input, StringIO(), reannotate_config, append=False)


@pytest.fixture
def preannotator_opts(base_input, base_config, mocker):
    return get_opts(base_input, StringIO(), base_config, skip_preannotators=False)


@pytest.fixture
def defaults_arguments_opts(base_input, defaults_arguments_config, mocker):
    return get_opts(base_input, StringIO(), defaults_arguments_config)


@pytest.fixture
def defaults_arguments_opts_alt(base_input, reannotate_config, mocker):
    return get_opts(base_input, StringIO(), reannotate_config, default_args='default:True')


@pytest.fixture
def virtuals_opts(base_input, virtuals_config, mocker):
    return get_opts(base_input, StringIO(), virtuals_config)


@pytest.fixture
def split_column_opts(split_column_input, base_config, mocker):
    return get_opts(split_column_input, StringIO(), base_config,
                    split='location', split_separator='|')


@pytest.fixture
def multiple_headers_opts(multiple_headers_input, base_config, mocker):
    return get_opts(multiple_headers_input, StringIO(), base_config,
                    split='location', split_separator='|')


@pytest.fixture
def base_multi_annotator(base_opts, mocker):
    return MultiAnnotator(base_opts, header=['id', 'location', 'variant'])


@pytest.fixture
def reannotate_multi_annotator(reannotate_opts, mocker):
    return MultiAnnotator(reannotate_opts, header=['id', 'location', 'variant'])


@pytest.fixture
def preannotator_multi_annotator(preannotator_opts, mocker):
    return MultiAnnotator(preannotator_opts, header=['id', 'location', 'variant'])


@pytest.fixture
def defaults_arguments_multi_annotator(defaults_arguments_opts,
                                       defaults_arguments_opts_alt, mocker):
    return (MultiAnnotator(defaults_arguments_opts, header=['id', 'location', 'variant']),
            MultiAnnotator(defaults_arguments_opts_alt, header=['id', 'location', 'variant']))


@pytest.fixture
def virtuals_multi_annotator(virtuals_opts, mocker):
    return MultiAnnotator(virtuals_opts, header=['id', 'location', 'variant'])


@pytest.fixture
def split_column_multi_annotator(split_column_opts, mocker):
    return MultiAnnotator(split_column_opts, header=['id', 'location', 'variant'])


@pytest.fixture
def multiple_headers_multi_annotator(multiple_headers_opts, mocker):
    return MultiAnnotator(multiple_headers_opts, header=['id', 'location', 'variant'])


@pytest.fixture
def base_input(mocker):
    return StringIO(deepcopy(input_output.BASE_INPUT))


@pytest.fixture
def split_column_input(mocker):
    return StringIO(deepcopy(input_output.SPLIT_COLUMN_INPUT))


@pytest.fixture
def multiple_headers_input(mocker):
    return StringIO(deepcopy(input_output.MULTIPLE_HEADERS_INPUT))


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


def test_base_config(base_opts, base_multi_annotator, base_output, mocker):
    with file_io.IOManager(base_opts, file_io.IOType.TSV, file_io.IOType.TSV) as IO_manager:
        base_multi_annotator.annotate_file(IO_manager)

        annotation_output = IO_manager.writer.outfile.getvalue()
        assert str(annotation_output) == str(base_output)


def test_reannotate(reannotate_opts, reannotate_multi_annotator, reannotate_output, mocker):
    with file_io.IOManager(reannotate_opts, file_io.IOType.TSV, file_io.IOType.TSV) as IO_manager:
        reannotate_multi_annotator.annotate_file(IO_manager)

        annotation_output = IO_manager.writer.outfile.getvalue()
        assert str(annotation_output) == str(reannotate_output)


def test_preannotator(preannotator_multi_annotator,
                      preannotator_opts, base_output, mocker):
    with file_io.IOManager(preannotator_opts, file_io.IOType.TSV, file_io.IOType.TSV) as IO_manager:
        preannotator_multi_annotator.annotate_file(IO_manager)

        annotation_output = IO_manager.writer.outfile.getvalue()
        assert str(annotation_output) == str(base_output)


def test_default_arguments(defaults_arguments_multi_annotator,
                           defaults_arguments_opts,
                           default_arguments_output, mocker):
    with file_io.IOManager(defaults_arguments_opts, file_io.IOType.TSV, file_io.IOType.TSV) as IO_manager:
        defaults_arguments_multi_annotator[0].annotate_file(IO_manager)

        annotation_output = IO_manager.writer.outfile.getvalue()
        assert str(annotation_output) == str(default_arguments_output)


def test_default_arguments_alt(defaults_arguments_multi_annotator,
                               defaults_arguments_opts_alt,
                               default_arguments_output, mocker):
    with file_io.IOManager(defaults_arguments_opts_alt, file_io.IOType.TSV, file_io.IOType.TSV) as IO_manager:
        defaults_arguments_multi_annotator[1].annotate_file(IO_manager)

        annotation_output = IO_manager.writer.outfile.getvalue()
        assert str(annotation_output) == str(default_arguments_output)


def test_virtuals(virtuals_multi_annotator, virtuals_opts, base_output, mocker):
    with file_io.IOManager(virtuals_opts, file_io.IOType.TSV, file_io.IOType.TSV) as IO_manager:
        virtuals_multi_annotator.annotate_file(IO_manager)

        annotation_output = IO_manager.writer.outfile.getvalue()
        assert str(annotation_output) == str(base_output)


def test_split_columns(split_column_multi_annotator, split_column_opts,
                       split_column_output, mocker):
    with file_io.IOManager(split_column_opts, file_io.IOType.TSV, file_io.IOType.TSV) as IO_manager:
        split_column_multi_annotator.annotate_file(IO_manager)

        annotation_output = IO_manager.writer.outfile.getvalue()
        assert str(annotation_output) == str(split_column_output)


def test_multiple_headers(multiple_headers_multi_annotator, multiple_headers_opts,
                          multiple_headers_output, mocker):
    with file_io.IOManager(multiple_headers_opts, file_io.IOType.TSV, file_io.IOType.TSV) as IO_manager:
        multiple_headers_multi_annotator.annotate_file(IO_manager)

        annotation_output = IO_manager.writer.outfile.getvalue()
        assert str(annotation_output) == str(multiple_headers_output)
