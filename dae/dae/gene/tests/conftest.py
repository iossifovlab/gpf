import pytest

import os
import shutil

from dae.utils.fixtures import change_environment

from dae.gene.denovo_gene_set_collection_factory import (
    DenovoGeneSetCollectionFactory,
)

from dae.utils.fixtures import path_to_fixtures as _path_to_fixtures


def fixtures_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures"))


def path_to_fixtures(*args):
    return _path_to_fixtures("gene", *args)


@pytest.fixture(scope="session")
def local_gpf_instance(gpf_instance):
    return gpf_instance(fixtures_dir())


@pytest.fixture(scope="session")
def dae_config_fixture(local_gpf_instance):
    return local_gpf_instance.dae_config


@pytest.fixture(scope="session")
def gene_info_config(local_gpf_instance):
    return local_gpf_instance._gene_info_config


# @pytest.fixture(scope="session")
# def gene_scores_db(local_gpf_instance):
#     return local_gpf_instance.gene_scores_db


@pytest.fixture(scope="session")
def denovo_gene_sets_db(local_gpf_instance):
    return local_gpf_instance.denovo_gene_sets_db


# @pytest.fixture(scope="session")
# def gene_sets_db(local_gpf_instance):
#     return local_gpf_instance.gene_sets_db


@pytest.fixture(scope="module")
def gene_info_cache_dir():
    cache_dir = path_to_fixtures("geneInfo", "cache")
    # assert not os.path.exists(
    #     cache_dir
    # ), 'Cache dir "{}" already  exists..'.format(cache_dir)
    os.makedirs(cache_dir, exist_ok=True)

    new_envs = {
        "DATA_STUDY_GROUPS_DENOVO_GENE_SETS_DIR": path_to_fixtures(
            "geneInfo", "cache"
        ),
        "DAE_DB_DIR": path_to_fixtures(),
    }

    for val in change_environment(new_envs):
        yield val

    shutil.rmtree(cache_dir)


@pytest.fixture(scope="session")
def genotype_data_names():
    return ["f1_group", "f2_group", "f3_group", "f4_trio"]


@pytest.fixture(scope="session")
def calc_gene_sets(request, local_gpf_instance, genotype_data_names):
    for dgs in genotype_data_names:
        genotype_data = local_gpf_instance.get_genotype_data(dgs)
        DenovoGeneSetCollectionFactory.build_collection(genotype_data)

    print("PRECALCULATION COMPLETE")

    def remove_gene_sets():
        for dgs in genotype_data_names:
            genotype_data = local_gpf_instance.get_genotype_data(dgs)
            cache_file = \
                DenovoGeneSetCollectionFactory.denovo_gene_set_cache_file(
                    genotype_data.config, "phenotype"
                )
            if os.path.exists(cache_file):
                os.remove(cache_file)

    request.addfinalizer(remove_gene_sets)


@pytest.fixture(scope="session")
def denovo_gene_sets(local_gpf_instance):
    return [
        DenovoGeneSetCollectionFactory.load_collection(
            local_gpf_instance.get_genotype_data("f1_group")
        ),
        DenovoGeneSetCollectionFactory.load_collection(
            local_gpf_instance.get_genotype_data("f2_group")
        ),
        DenovoGeneSetCollectionFactory.load_collection(
            local_gpf_instance.get_genotype_data("f3_group")
        ),
    ]


@pytest.fixture(scope="session")
def denovo_gene_set_f4(local_gpf_instance):
    return DenovoGeneSetCollectionFactory.load_collection(
        local_gpf_instance.get_genotype_data("f4_trio")
    )


@pytest.fixture(scope="session")
def f4_trio_denovo_gene_set_config(local_gpf_instance):
    return local_gpf_instance.get_genotype_data_config("f4_trio")
