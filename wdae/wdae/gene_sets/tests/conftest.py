import os
import pytest

from dae.gpf_instance.gpf_instance import GPFInstance

from dae.gene.denovo_gene_set_config import DenovoGeneSetConfigParser
from dae.gene.denovo_gene_set import DenovoGeneSet

from datasets_api.studies_manager import StudiesManager


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture(scope='function')
def gpf_instance():
    return GPFInstance(work_dir=fixtures_dir())


@pytest.fixture(scope='function')
def variants_db_fixture(gpf_instance):
    return gpf_instance.variants_db


@pytest.fixture(scope='function')
def studies_manager(gpf_instance):
    return StudiesManager(gpf_instance)


@pytest.fixture(scope='function')
def mock_studies_manager(db, mocker, studies_manager):
    mocker.patch(
        'gene_sets.views.get_studies_manager',
        return_value=studies_manager)
    mocker.patch(
        'datasets_api.permissions.get_studies_manager',
        return_value=studies_manager)


@pytest.fixture(scope='function')
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


@pytest.fixture(scope='function')
def denovo_gene_sets(variants_db_fixture):
    return [
        get_denovo_gene_set_by_id(variants_db_fixture, 'f1_group'),
        get_denovo_gene_set_by_id(variants_db_fixture, 'f2_group'),
        get_denovo_gene_set_by_id(variants_db_fixture, 'f3_group')
    ]
