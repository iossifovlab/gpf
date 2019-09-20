import pytest

import os
import shutil

from dae.gpf_instance.gpf_instance import GPFInstance

from dae.utils.fixtures import change_environment

from dae.gene.denovo_gene_set_config import DenovoGeneSetConfigParser
from dae.gene.denovo_gene_set import DenovoGeneSet

from dae.utils.fixtures import path_to_fixtures as _path_to_fixtures


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


def path_to_fixtures(*args):
    return _path_to_fixtures('gene', *args)


def mock_property(mocker):
    def result(property, mock_value):
        file_mock = mocker.patch(property, new_callable=mocker.PropertyMock)
        file_mock.return_value = mock_value
    return result


@pytest.fixture(scope='function')
def gpf_instance(mock_genomes_db):
    return GPFInstance(work_dir=fixtures_dir())


@pytest.fixture(scope='function')
def dae_config_fixture(gpf_instance):
    return gpf_instance.dae_config


@pytest.fixture(scope='function')
def variants_db_fixture(gpf_instance):
    return gpf_instance.variants_db


@pytest.fixture(scope='function')
def gene_info_config(gpf_instance):
    return gpf_instance.gene_info_config


@pytest.fixture(scope='function')
def weights_factory(gpf_instance):
    return gpf_instance.weights_factory


@pytest.fixture(scope='function')
def score_config(gpf_instance):
    return gpf_instance.score_config


@pytest.fixture(scope='function')
def scores_factory(gpf_instance):
    return gpf_instance.scores_factory


@pytest.fixture(scope='function')
def denovo_gene_set_facade(gpf_instance):
    return gpf_instance.denovo_gene_set_facade


@pytest.fixture(scope='module')
def gene_info_cache_dir():
    cache_dir = path_to_fixtures('geneInfo', 'cache')
    assert not os.path.exists(cache_dir), \
        'Cache dir "{}"already  exists..'.format(cache_dir)
    os.makedirs(cache_dir)

    new_envs = {
        'DATA_STUDY_GROUPS_DENOVO_GENE_SETS_DIR':
            path_to_fixtures('geneInfo', 'cache'),
        'DAE_DB_DIR':
            path_to_fixtures()
    }

    for val in change_environment(new_envs):
        yield val

    shutil.rmtree(cache_dir)


@pytest.fixture(scope='function')
def calc_gene_sets(request, denovo_gene_sets, denovo_gene_set_f4):
    for dgs in denovo_gene_sets + [denovo_gene_set_f4]:
        dgs.load(build_cache=True)

    print("PRECALCULATION COMPLETE")

    def remove_gene_sets():
        for dgs in denovo_gene_sets + [denovo_gene_set_f4]:
            os.remove(DenovoGeneSetConfigParser.denovo_gene_set_cache_file(
                dgs.config, 'phenotype'))
    request.addfinalizer(remove_gene_sets)


def get_denovo_gene_set_by_id(variants_db_fixture, dgs_id):
    denovo_gene_set_config = DenovoGeneSetConfigParser.parse(
        variants_db_fixture.get_config(dgs_id))

    return DenovoGeneSet(
        variants_db_fixture.get(dgs_id), denovo_gene_set_config
    )


@pytest.fixture(scope='function')
def denovo_gene_sets(variants_db_fixture):
    return [
        get_denovo_gene_set_by_id(variants_db_fixture, 'f1_group'),
        get_denovo_gene_set_by_id(variants_db_fixture, 'f2_group'),
        get_denovo_gene_set_by_id(variants_db_fixture, 'f3_group')
    ]


@pytest.fixture(scope='function')
def denovo_gene_set_f4(variants_db_fixture):
    return get_denovo_gene_set_by_id(variants_db_fixture, 'f4_trio')


@pytest.fixture(scope='function')
def f4_trio_denovo_gene_set_config(variants_db_fixture):
    return DenovoGeneSetConfigParser.parse(
        variants_db_fixture.get_config('f4_trio')
    )
