import pytest
from copy import deepcopy
from io import StringIO
from builtins import str

from annotation.annotation_pipeline_cluster import main
from annotation.tests import configs
from annotation.tests import input_output


class MyStringIO(StringIO):

    def __add__(self, other):
        return self

    def replace(self, first, second):
        return second


def open_config(filename, mode):
    return variant_db_config()


@pytest.fixture
def config():
    return deepcopy(input_output.CONFIG)


def variant_db_config():
    return MyStringIO(deepcopy(configs.VARIANT_DB_CONFIG))


@pytest.fixture
def data_dir():
    return deepcopy(input_output.DATA_DIR)


@pytest.fixture
def output_dir():
    return deepcopy(input_output.OUTPUT_DIR)


@pytest.fixture
def sge_rreq():
    return deepcopy(input_output.SGE_RREQ)


@pytest.fixture
def output():
    return deepcopy(input_output.MAKEFILE_OUTPUT)


@pytest.fixture
def os_walk(data_dir):
    return [
        (data_dir + '/cccc', [],
         ['DENOVO_STUDY', 'OTHER_STUDY', 'TRANSMITTED_STUDY']),
        (data_dir + '/cccc/DENOVO_STUDY', [],
         ['families.tsv', 'data_annotated.tsv']),
        (data_dir + '/cccc/OTHER_STUDY', [],
         ['families.tsv', 'data_annotated.tsv']),
        (data_dir + '/cccc/TRANSMITTED_STUDY', [],
         ['famData.txt', 'temp.file', 'TRANSMITTED_STUDY.format-annot'])]


def return_input(*args, **kwargs):
    return args[0]


def test_annotation_pipeline_cluster(config, data_dir, output_dir, sge_rreq,
                                     output, os_walk, mocker, capsys):
    mocker.patch('os.path.abspath', side_effect=return_input)
    mocker.patch(
        'annotation.annotation_pipeline_cluster.open', side_effect=open_config)
    mocker.patch('os.walk', side_effect=lambda path: os_walk)
    mocker.patch('annotation.annotation_pipeline_cluster.'
                 'VariantDBConf._validate', return_value=None)
    main(config, data_dir, output_dir, sge_rreq)

    a = str(capsys.readouterr().out)
    b = str(output)

    print(('a', a))
    print(('b', b))
    assert a == b
