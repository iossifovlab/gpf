import os
import pytest

from dae.gpf_instance.gpf_instance import GPFInstance
from gpf_instance.gpf_instance import reload_datasets

from dae.gene.denovo_gene_set_config import DenovoGeneSetConfigParser
from dae.gene.denovo_gene_set import DenovoGeneSet


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture(scope='session')
def gpf_instance(mock_genomes_db):
    return GPFInstance(work_dir=fixtures_dir())


@pytest.fixture(scope='session')
def variants_db_fixture(gpf_instance):
    return gpf_instance.variants_db


@pytest.fixture(scope='function')
def mock_gpf_instance(db, mocker, gpf_instance):
    reload_datasets(gpf_instance.variants_db)
    mocker.patch(
        'query_base.query_base.get_gpf_instance',
        return_value=gpf_instance
    )
    mocker.patch(
        'datasets_api.permissions.get_gpf_instance',
        return_value=gpf_instance
    )


@pytest.fixture(scope='session')
def calc_gene_sets(request, denovo_gene_sets):
    for dgs in denovo_gene_sets:
        dgs.load(build_cache=True)

    print("PRECALCULATION COMPLETE")

    def remove_gene_sets():
        for dgs in denovo_gene_sets:
            os.remove(DenovoGeneSetConfigParser.denovo_gene_set_cache_file(
                dgs.config, 'phenotype'))
    request.addfinalizer(remove_gene_sets)


def get_denovo_gene_set_by_id(variants_db_fixture, dgs_id):
    denovo_gene_set_config = DenovoGeneSetConfigParser.parse(
        variants_db_fixture.get_config(dgs_id)
    )

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
