import os
import pytest

from dae.gpf_instance.gpf_instance import GPFInstance
from gpf_instance.gpf_instance import reload_datasets

from dae.gene.denovo_gene_set_config import DenovoGeneSetConfigParser
from dae.gene.denovo_gene_set_collection_factory import \
    DenovoGeneSetCollectionFactory


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture(scope='session')
def gpf_instance(mock_genomes_db):
    return GPFInstance(work_dir=fixtures_dir())


@pytest.fixture(scope='session')
def variants_db_fixture(gpf_instance):
    return gpf_instance._variants_db


@pytest.fixture(scope='function')
def mock_gpf_instance(db, mocker, gpf_instance):
    reload_datasets(gpf_instance._variants_db)
    mocker.patch(
        'query_base.query_base.get_gpf_instance',
        return_value=gpf_instance
    )
    mocker.patch(
        'datasets_api.permissions.get_gpf_instance',
        return_value=gpf_instance
    )


@pytest.fixture(scope='session')
def genotype_data_names():
    return ['f1_group', 'f2_group', 'f3_group']


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
