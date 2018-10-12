import pytest
from io import StringIO
from box import Box
from annotation.tools.file_io import Schema

from annotation.annotation_pipeline import MultiAnnotator,\
    MyConfigParser, str_to_class
from annotation.tools.duplicate_columns import\
    DuplicateColumnsAnnotator


class Annotator(object):

    def __init__(self, options, header):
        self.default = options['default']

    def line_annotations(self, line, new_columns):
        if self.default:
            return ['def_arg:' + line[1]]
        else:
            result = []
            for c in new_columns:
                if c == 'location':
                    result.append(line[1])
                elif c == 'variant':
                    result.append(line[2])
            return result

    # TODO
    # The following properties are currently useless.
    # Perhaps use them for schema testing?
    @property
    def schema(self):
        return Schema()

    @property
    def new_columns(self):
        return ['TEST:score']


class Preannotator(object):

    def __init__(self):
        pass

    @property
    def new_columns(self):
        return ['TEST:location']

    def line_annotations(self, line, new_columns):
        return ['test:' + line[1]]

    @property
    def schema(self):
        return Schema()


class DummyIOAdapter(object):

    def __init__(self, input_):
        self.input = input_
        self.output = []

    def lines_read(self):
        for line in self.input:
            yield line

    def line_write(self, input_):
        self.output.append(input_)

    def header_write(self, input_):
        self.output.append(input_)


@pytest.fixture(autouse=True)
def mock(mocker):
    mocker.patch.object(MyConfigParser, 'read', MyConfigParser.readfp)
    mocker.patch('annotation.annotation_pipeline.str_to_class',
                 return_value=Annotator)
    mocker.patch('annotation.annotation_pipeline.PreannotatorLoader.load_preannotators',
                 return_value=[Preannotator()])
    mocker.patch('annotation.annotation_pipeline.exists',
                 return_value=True)


def get_opts(config, append=True,
             split=None, split_separator=',',
             skip_preannotators=True, default_args='default:False'):
    options = {
        'config': StringIO(config),
        'append': append,
        'split': split,
        'separator': split_separator,
        'skip_preannotators': skip_preannotators,
        'default_arguments': default_args,
        'no_header': True,
    }
    return Box(options, default_box=True, default_box_attr=None)


def input_base():
    return [
        ['1', '4:4372372973', 'sub(A->C)'],
        ['5', '10:4372372973', 'sub(G->A)'],
        ['3', 'X:4372', 'ins(AAA)'],
        ['6', 'Y:4372372973', 'del(2)']
    ]


def input_split_column():
    return [
        ['5', '10:4372372973,1:8493943843', 'sub(G->A)'],
    ]


def input_multiple_headers():
    input_ = input_base()
    input_.insert(0, ['#Second header'])
    input_.insert(3, ['#Last header'])
    return input_


def output_base():
    return [
        ['#id', 'location', 'variant', 'loc'],
        ['1', '4:4372372973', 'sub(A->C)', '4:4372372973'],
        ['5', '10:4372372973', 'sub(G->A)', '10:4372372973'],
        ['3', 'X:4372', 'ins(AAA)', 'X:4372'],
        ['6', 'Y:4372372973', 'del(2)', 'Y:4372372973']
    ]


def output_reannotate():
    return [
        ['#id', 'location', 'variant'],
        ['1', 'def_arg:4:4372372973', 'sub(A->C)'],
        ['5', 'def_arg:10:4372372973', 'sub(G->A)'],
        ['3', 'def_arg:X:4372', 'ins(AAA)'],
        ['6', 'def_arg:Y:4372372973', 'del(2)']
    ]


def output_default_args():
    return [line[:-1] + ['def_arg:' + line[1]]
            for line in output_base()]


def output_split_column():
    return [
        ['#id', 'location', 'variant', 'loc'],
        ['5', '10:4372372973,1:8493943843', 'sub(G->A)', '10:4372372973,1:8493943843'],
    ]


def output_multiple_headers():
    output = output_base()
    output.insert(1, ['#Second header'])
    output.insert(4, ['#Last header'])
    return output


def options_base():
    config = (
        '[Add location]\n'
        'options.columns=location\n'
        'columns.location=loc\n')
    return get_opts(config)


def options_reannotate():
    config = (
        '[Reannotate location]\n'
        'options.columns=location\n'
        'columns.location=location\n')
    return get_opts(config, append=False, default_args='default:True')


def options_preannotate():
    config = (
        '[Add location]\n'
        'options.columns=location\n'
        'columns.location=loc\n')
    return get_opts(config, skip_preannotators=False)


def options_default_args():
    config = (
        '[Add location]\n'
        'options.columns=location\n'
        'columns.location=def_arg:location\n'
        'options.default=True\n')
    return get_opts(config)


def options_default_args_alt():
    config = (
        '[Reannotate location]\n'
        'options.columns=location\n'
        'columns.location=def_arg:location\n')
    return get_opts(config, default_args='default:True')


def options_virtuals():
    config = (
        '[Add location]\n'
        'options.columns=location,variant\n'
        'columns.location=loc\n'
        'columns.variant=var\n'
        'virtuals=variant\n')
    return get_opts(config)


def options_split_column():
    config = (
        '[Add location]\n'
        'options.columns=location\n'
        'columns.location=loc\n')
    return get_opts(config, split='location', split_separator='|')


def options_multiple_headers():
    config = (
        '[Add location]\n'
        'options.columns=location\n'
        'columns.location=loc\n')
    return get_opts(config, split='location', split_separator='|')


def test_str_to_class():
    assert str_to_class('duplicate_columns.DuplicateColumnsAnnotator') ==\
        DuplicateColumnsAnnotator


@pytest.mark.parametrize('input_file,options,expected_output', [
    (input_base(), options_base(), output_base()),
    (input_base(), options_reannotate(), output_reannotate()),
    (input_base(), options_preannotate(), output_base()),
    (input_base(), options_default_args(), output_default_args()),
    (input_base(), options_default_args_alt(), output_default_args()),
    (input_base(), options_virtuals(), output_base()),
    (input_split_column(), options_split_column(), output_split_column()),
    (input_multiple_headers(), options_multiple_headers(), output_multiple_headers())
])
def test_annotators_tsv(input_file, options, expected_output):
    io = DummyIOAdapter(input_file)
    annotator = MultiAnnotator(options, header=['id', 'location', 'variant'])
    annotator.annotate_file(io)
    assert io.output == expected_output
