import pytest

import os
import shutil

from dae.utils.fixtures import change_environment

from dae.gene.denovo_gene_set_collection_factory import (
    DenovoGeneSetCollectionFactory,
)

from dae.gene.gene_scores import GeneScoresDb, GeneScore
from dae.gene.gene_sets_db import GeneSetCollection, GeneSetsDb

from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo
from dae.genomic_resources.repository import GR_CONF_FILE_NAME

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
def score_config(local_gpf_instance):
    return local_gpf_instance._score_config


@pytest.fixture(scope="session")
def scores_factory(local_gpf_instance):
    return local_gpf_instance._scores_factory


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


@pytest.fixture(scope="session")
def scores_repo():
    dae_dir = fixtures_dir()
    with open(
        os.path.join(dae_dir, "geneInfo", "GeneScores", "RVIS.csv")
    ) as f:
        RVIS_content = f.read()
    with open(
        os.path.join(dae_dir, "geneInfo", "GeneScores", "LGD.csv")
    ) as f:
        LGD_content = f.read()

    scores_repo = GenomicResourceEmbededRepo("scores", content={
        "RVIS_rank": {
            GR_CONF_FILE_NAME: (
                "type: gene_score\n"
                "id: RVIS_rank\n"
                "filename: RVIS.csv\n"
                "desc: RVIS rank\n"
                "histogram:\n"
                "  bins: 150\n"
                "  xscale: linear\n"
                "  yscale: linear\n"
            ),
            "RVIS.csv": RVIS_content
        },
        "LGD_rank": {
            GR_CONF_FILE_NAME: (
                "type: gene_score\n"
                "id: LGD_rank\n"
                "filename: LGD.csv\n"
                "desc: LGD rank\n"
                "histogram:\n"
                "  bins: 150\n"
                "  xscale: linear\n"
                "  yscale: linear\n"
            ),
            "LGD.csv": LGD_content
        }
    })
    return scores_repo


@pytest.fixture(scope="session")
def gene_sets_repo():
    sets_repo = GenomicResourceEmbededRepo("gene_sets", content={
        "main": {
            GR_CONF_FILE_NAME: (
                "type: gene_set\n"
                "id: main\n"
                "format: directory\n"
                "directory: GeneSets\n"
                "web_label: Main\n"
                "web_format_str: \"key| (|count|): |desc\"\n"
            ),
            "GeneSets": {
                "main_candidates.txt": (
                    "Main Candidates\n"
                    "POGZ\n"
                    "CHD8\n"
                    "ANK2\n"
                    "FAT4\n"
                    "NBEA\n"
                    "CELSR1\n"
                    "USP7\n"
                    "GOLGA5\n"
                    "PCSK2\n"
                )
            }
        },
        "test_mapping": {
            GR_CONF_FILE_NAME: (
                "type: gene_set\n"
                "id: test_mapping\n"
                "format: map\n"
                "filename: test-map.txt\n"
                "web_label: Test mapping\n"
                "web_format_str: \"key| (|count|)\"\n"
            ),
            "test-map.txt": (
                "#geneNS\tsym\n"
                "POGZ\ttest:01 test:02\n"
                "CHD8\ttest:02 test:03\n"
            ),
            "test-mapnames.txt": (
                "test:01\ttest_first\n"
                "test:02\ttest_second\n"
                "test:03\ttest_third\n"
            )
        },
        "test_gmt": {
            GR_CONF_FILE_NAME: (
                "type: gene_set\n"
                "id: test_gmt\n"
                "format: gmt\n"
                "filename: test-gmt.gmt\n"
                "web_label: Test GMT\n"
                "web_format_str: \"key| (|count|)\"\n"
            ),
            "test-gmt.gmt": (
                "TEST_GENE_SET1\tsomedescription\tPOGZ\tCHD8\n"
                "TEST_GENE_SET2\tsomedescription\tANK2\tFAT4\n"
                "TEST_GENE_SET3\tsomedescription\tPOGZ\n"
            )
        }
    })
    return sets_repo


@pytest.fixture(scope="session")
def gene_scores_db(scores_repo):
    resources = [
        scores_repo.get_resource("LGD_rank"),
        scores_repo.get_resource("RVIS_rank"),
    ]
    scores = [GeneScore.load_gene_score_from_resource(r) for r in resources]
    return GeneScoresDb(scores)


@pytest.fixture(scope="session")
def gene_sets_db(gene_sets_repo):
    resources = [
        gene_sets_repo.get_resource("main"),
        gene_sets_repo.get_resource("test_mapping"),
        gene_sets_repo.get_resource("test_gmt"),
    ]
    gene_set_collections = [
        GeneSetCollection.from_resource(r) for r in resources
    ]
    return GeneSetsDb(gene_set_collections)
