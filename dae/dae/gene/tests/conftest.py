import pytest

import os
import shutil

from dae.gpf_instance.gpf_instance import GPFInstance

from dae.utils.fixtures import change_environment

from dae.gene.denovo_gene_set_config import DenovoGeneSetConfigParser
from dae.gene.denovo_gene_set_collection_factory import \
    DenovoGeneSetCollectionFactory

from dae.utils.fixtures import path_to_fixtures as _path_to_fixtures


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


def path_to_fixtures(*args):
    return _path_to_fixtures('gene', *args)


@pytest.fixture(scope='session')
def local_gpf_instance(gpf_instance):
    return gpf_instance(fixtures_dir())


@pytest.fixture(scope='session')
def dae_config_fixture(local_gpf_instance):
    return local_gpf_instance.dae_config


@pytest.fixture(scope='session')
def variants_db_fixture(local_gpf_instance):
    return local_gpf_instance._variants_db


@pytest.fixture(scope='session')
def gene_info_config(local_gpf_instance):
    return local_gpf_instance._gene_info_config


@pytest.fixture(scope='session')
def gene_weights_db(local_gpf_instance):
    return local_gpf_instance.gene_weights_db


@pytest.fixture(scope='session')
def score_config(local_gpf_instance):
    return local_gpf_instance._score_config


@pytest.fixture(scope='session')
def scores_factory(local_gpf_instance):
    return local_gpf_instance._scores_factory


@pytest.fixture(scope='session')
def denovo_gene_sets_db(local_gpf_instance):
    return local_gpf_instance.denovo_gene_sets_db


@pytest.fixture(scope='session')
def gene_sets_db(local_gpf_instance):
    return local_gpf_instance.gene_sets_db


@pytest.fixture(scope='module')
def gene_info_cache_dir():
    cache_dir = path_to_fixtures('geneInfo', 'cache')
    assert not os.path.exists(cache_dir), \
        'Cache dir "{}" already  exists..'.format(cache_dir)
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
def genotype_data_names():
    return ['f1_group', 'f2_group', 'f3_group', 'f4_trio']


@pytest.fixture(scope='session')
def calc_gene_sets(request, variants_db_fixture, genotype_data_names):
    for dgs in genotype_data_names:
        genotype_data = variants_db_fixture.get(dgs)
        DenovoGeneSetCollectionFactory.build_collection(genotype_data)

    print("PRECALCULATION COMPLETE")

    def remove_gene_sets():
        for dgs in genotype_data_names:
            genotype_data = variants_db_fixture.get(dgs)
            config = DenovoGeneSetConfigParser.parse(genotype_data.config)
            os.remove(DenovoGeneSetConfigParser.denovo_gene_set_cache_file(
                config, 'phenotype')
            )
    request.addfinalizer(remove_gene_sets)


@pytest.fixture(scope='session')
def denovo_gene_sets(variants_db_fixture):
    return [
        DenovoGeneSetCollectionFactory.load_collection(
            variants_db_fixture.get('f1_group')),
        DenovoGeneSetCollectionFactory.load_collection(
            variants_db_fixture.get('f2_group')),
        DenovoGeneSetCollectionFactory.load_collection(
            variants_db_fixture.get('f3_group')),
    ]


@pytest.fixture(scope='session')
def denovo_gene_set_f4(variants_db_fixture):
    return DenovoGeneSetCollectionFactory.load_collection(
        variants_db_fixture.get('f4_trio')
    )


@pytest.fixture(scope='session')
def f4_trio_denovo_gene_set_config(variants_db_fixture):
    return DenovoGeneSetConfigParser.parse(
        variants_db_fixture.get_config('f4_trio')
    )
