# pylint: disable=W0621,C0114,C0116,W0212,W0613

import os
import shutil
from collections.abc import Iterator
from typing import Any, Callable, List, cast

import pytest

from dae.gene_sets.denovo_gene_set_collection import DenovoGeneSetCollection
from dae.gene_sets.denovo_gene_set_collection_factory import (
    DenovoGeneSetCollectionFactory,
)
from dae.gene_sets.denovo_gene_sets_db import DenovoGeneSetsDb
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData
from dae.testing import denovo_study, setup_denovo, setup_pedigree
from dae.testing.foobar_import import foobar_gpf
from dae.utils.fixtures import change_environment
from dae.utils.fixtures import path_to_fixtures as _path_to_fixtures


def fixtures_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures"))


def path_to_fixtures(*args: Any) -> str:
    return cast(str, _path_to_fixtures("gene", *args))


@pytest.fixture(scope="session")
def local_gpf_instance(
    gpf_instance: Callable[[Any], GPFInstance],
) -> GPFInstance:
    return gpf_instance(
        os.path.join(fixtures_dir(), "gpf_instance.yaml"))


# @pytest.fixture(scope="session")
# def dae_config_fixture(local_gpf_instance):
#     return local_gpf_instance.dae_config


# @pytest.fixture(scope="session")
# def gene_info_config(local_gpf_instance):
#     return local_gpf_instance._gene_info_config


# @pytest.fixture(scope="session")
# def gene_scores_db(local_gpf_instance):
#     return local_gpf_instance.gene_scores_db


@pytest.fixture(scope="session")
def denovo_gene_sets_db(local_gpf_instance: GPFInstance) -> DenovoGeneSetsDb:
    return local_gpf_instance.denovo_gene_sets_db


# @pytest.fixture(scope="session")
# def gene_sets_db(local_gpf_instance):
#     return local_gpf_instance.gene_sets_db


@pytest.fixture(scope="module")
def gene_info_cache_dir() -> Iterator[None]:
    cache_dir = path_to_fixtures("geneInfo", "cache")
    # assert not os.path.exists(
    #     cache_dir
    # ), 'Cache dir "{}" already  exists..'.format(cache_dir)
    os.makedirs(cache_dir, exist_ok=True)

    new_envs = {
        "DATA_STUDY_GROUPS_DENOVO_GENE_SETS_DIR": path_to_fixtures(
            "geneInfo", "cache",
        ),
        "DAE_DB_DIR": path_to_fixtures(),
    }

    for val in change_environment(new_envs):
        yield val

    shutil.rmtree(cache_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def genotype_data_names() -> List[str]:
    return ["f1_group", "f2_group", "f3_group", "f4_trio"]


@pytest.fixture(scope="session")
def calc_gene_sets(
    request: pytest.FixtureRequest,
    local_gpf_instance: GPFInstance,
    genotype_data_names: List[str],
) -> None:
    for dgs in genotype_data_names:
        genotype_data = local_gpf_instance.get_genotype_data(dgs)
        DenovoGeneSetCollectionFactory.build_collection(genotype_data)

    print("PRECALCULATION COMPLETE")

    def remove_gene_sets() -> None:
        for dgs in genotype_data_names:
            genotype_data = local_gpf_instance.get_genotype_data(dgs)
            cache_file = \
                DenovoGeneSetCollectionFactory.denovo_gene_set_cache_file(
                    genotype_data.config, "phenotype",
                )
            if os.path.exists(cache_file):
                os.remove(cache_file)

    request.addfinalizer(remove_gene_sets)  # type: ignore


@pytest.fixture(scope="session")
def denovo_gene_sets(
    local_gpf_instance: GPFInstance,
) -> list[DenovoGeneSetCollection]:
    return [
        DenovoGeneSetCollectionFactory.load_collection(
            local_gpf_instance.get_genotype_data("f1_group"),
        ),
        DenovoGeneSetCollectionFactory.load_collection(
            local_gpf_instance.get_genotype_data("f2_group"),
        ),
        DenovoGeneSetCollectionFactory.load_collection(
            local_gpf_instance.get_genotype_data("f3_group"),
        ),
    ]


@pytest.fixture(scope="session")
def denovo_gene_set_f4(
    local_gpf_instance: GPFInstance,
) -> DenovoGeneSetCollection:
    return cast(
        DenovoGeneSetCollection,
        DenovoGeneSetCollectionFactory.load_collection(
            local_gpf_instance.get_genotype_data("f4_trio")))


# @pytest.fixture(scope="session")
# def f4_trio_denovo_gene_set_config(local_gpf_instance):
#     return local_gpf_instance.get_genotype_data_config("f4_trio")


@pytest.fixture()
def trios2_study(
    tmp_path_factory: pytest.TempPathFactory,
) -> GenotypeData:
    root_path = tmp_path_factory.mktemp(
        "denovo_gene_sets_tios")
    gpf_instance = foobar_gpf(root_path)
    ped_path = setup_pedigree(
        root_path / "trios2_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        f1       s1       d1     m1     2   1      sib
        f2       m2       0      0      2   1      mom
        f2       d2       0      0      1   1      dad
        f2       p2       d2     m2     2   2      prb
        """)
    vcf_path = setup_denovo(
        root_path / "trios2_data" / "in.tsv",
        """
          familyId  location  variant    bestState
          f1        foo:7     sub(A->G)  2||2||1||2/0||0||1||0
          f1        foo:14    sub(C->T)  2||2||2||1/0||0||0||1
          f2        bar:7     ins(CCCC)  2||2||1/0||0||1
          f2        bar:7     sub(C->A)  2||2||1/0||0||1
          f1        bar:7     sub(C->T)  2||2||1||2/0||0||1||0
        """,
    )

    study = denovo_study(
        root_path,
        "trios2", ped_path, [vcf_path],
        gpf_instance,
        study_config_update={
            "id": "trios2",
            "denovo_gene_sets": {
                "enabled": True,
            },
        })
    return study
