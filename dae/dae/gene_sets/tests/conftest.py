# pylint: disable=W0621,C0114,C0116,W0212,W0613

import os
from typing import Any, cast

import pytest

from dae.gene_sets.denovo_gene_set_collection import DenovoGeneSetCollection
from dae.gene_sets.denovo_gene_set_helpers import (
    DenovoGeneSetHelpers,
)
from dae.gene_sets.denovo_gene_sets_db import DenovoGeneSetsDb
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData
from dae.testing import denovo_study, setup_denovo, setup_pedigree
from dae.testing.foobar_import import foobar_gpf
from dae.utils.fixtures import path_to_fixtures as _path_to_fixtures


def fixtures_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures"))


def path_to_fixtures(*args: Any) -> str:
    return cast(str, _path_to_fixtures("gene", *args))


@pytest.fixture(scope="session")
def t4c8_denovo_gene_sets(
    t4c8_instance: GPFInstance,
) -> list[DenovoGeneSetCollection]:
    result = [
        DenovoGeneSetHelpers.load_collection(
            t4c8_instance.get_genotype_data("t4c8_study_1"),
        ),
        DenovoGeneSetHelpers.load_collection(
            t4c8_instance.get_genotype_data("t4c8_study_2"),
        ),
        DenovoGeneSetHelpers.load_collection(
            t4c8_instance.get_genotype_data("t4c8_study_4"),
        ),
    ]
    return list(filter(None, result))


@pytest.fixture(scope="session")
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

    return denovo_study(
        root_path,
        "trios2", ped_path, [vcf_path],
        gpf_instance,
        study_config_update={
            "id": "trios2",
            "denovo_gene_sets": {
                "enabled": True,
            },
        })


@pytest.fixture(scope="session")
def trios2_dgsc(
    trios2_study: GenotypeData,
) -> DenovoGeneSetCollection:
    DenovoGeneSetHelpers.build_collection(trios2_study)
    result = DenovoGeneSetHelpers.load_collection(trios2_study)
    assert result is not None
    return result


@pytest.fixture(scope="session")
def t4c8_denovo_gene_sets_db(
    t4c8_instance: GPFInstance,
) -> DenovoGeneSetsDb:
    return t4c8_instance.denovo_gene_sets_db
