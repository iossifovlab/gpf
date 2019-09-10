'''
Created on Mar 29, 2018

@author: lubo
'''
import os
import shutil

import pytest

from dae.utils.fixtures import change_environment

from dae.gene.gene_info_config import GeneInfoConfigParser
from dae.gene.score_config_parser import ScoreConfigParser
from dae.gene.denovo_gene_set_config import DenovoGeneSetConfigParser
from dae.gene.denovo_gene_set import DenovoGeneSet
from dae.gene.denovo_gene_set_facade import DenovoGeneSetFacade
from dae.gene.weights import WeightsLoader
from dae.gene.scores import ScoreLoader

from dae.utils.fixtures import path_to_fixtures as _path_to_fixtures
# Used by pytest
from dae.configuration.dae_config_parser import DAEConfigParser
from dae.studies.variants_db import VariantsDb


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


@pytest.fixture(scope='session')
def gene_info_config(dae_config_fixture):
    gene_info_config = GeneInfoConfigParser.read_and_parse_file_configuration(
        dae_config_fixture.gene_info_db.conf_file,
        dae_config_fixture.dae_data_dir
    )
    return gene_info_config


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


@pytest.fixture(scope='session')
def calc_gene_sets(request, denovo_gene_sets, denovo_gene_set_f4):
    for dgs in denovo_gene_sets + [denovo_gene_set_f4]:
        dgs.load(build_cache=True)

    print("PRECALCULATION COMPLETE")

    def remove_gene_sets():
        for dgs in denovo_gene_sets + [denovo_gene_set_f4]:
            os.remove(DenovoGeneSetConfigParser.denovo_gene_set_cache_file(
                dgs.config, 'phenotype'))
    request.addfinalizer(remove_gene_sets)


@pytest.fixture(scope='session')
def weights_loader(gene_info_config):
    return WeightsLoader(config=gene_info_config.gene_weights)


@pytest.fixture(scope='session')
def score_config(dae_config_fixture):
    return ScoreConfigParser.read_and_parse_file_configuration(
        dae_config_fixture.genomic_scores_db.conf_file,
        dae_config_fixture.dae_data_dir
    )


@pytest.fixture(scope='session')
def score_loader(score_config):
    return ScoreLoader(score_config)


@pytest.fixture(scope='session')
def dae_config_fixture():
    dae_config = DAEConfigParser.read_and_parse_file_configuration(
        work_dir=fixtures_dir())
    return dae_config


@pytest.fixture(scope='session')
def variants_db_fixture(dae_config_fixture):
    vdb = VariantsDb(dae_config_fixture)
    return vdb


def get_denovo_gene_set_by_id(variants_db_fixture, dgs_id):
    denovo_gene_set_config = DenovoGeneSetConfigParser.parse(
        variants_db_fixture.get_config(dgs_id))

    return DenovoGeneSet(
        variants_db_fixture.get(dgs_id), denovo_gene_set_config
    )


@pytest.fixture(scope='session')
def denovo_gene_sets(variants_db_fixture):
    return [
        get_denovo_gene_set_by_id(variants_db_fixture, 'f1_group'),
        get_denovo_gene_set_by_id(variants_db_fixture, 'f2_group'),
        get_denovo_gene_set_by_id(variants_db_fixture, 'f3_group')
    ]


@pytest.fixture(scope='session')
def denovo_gene_set_f4(variants_db_fixture):
    return get_denovo_gene_set_by_id(variants_db_fixture, 'f4_trio')


@pytest.fixture(scope='session')
def denovo_gene_set_facade(variants_db_fixture):
    return DenovoGeneSetFacade(variants_db_fixture)


@pytest.fixture(scope='session')
def f4_trio_denovo_gene_set_config(variants_db_fixture):
    return DenovoGeneSetConfigParser.parse(
        variants_db_fixture.get_config('f4_trio')
    )
