import pytest

from gpf_instance.gpf_instance import reload_datasets

from dae.gene.denovo_gene_set_collection_factory import \
    DenovoGeneSetCollectionFactory


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
def denovo_gene_sets(variants_db_fixture):
    return [
        DenovoGeneSetCollectionFactory.load_collection(
            variants_db_fixture.get('f1_group')),
        DenovoGeneSetCollectionFactory.load_collection(
            variants_db_fixture.get('f2_group')),
        DenovoGeneSetCollectionFactory.load_collection(
            variants_db_fixture.get('f3_group')),
    ]
