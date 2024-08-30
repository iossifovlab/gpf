# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from collections.abc import Callable
from typing import cast

import pytest

from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing import denovo_study, setup_denovo, setup_pedigree
from dae.testing.foobar_import import foobar_gpf
from dae.variants.attributes import Inheritance
from dae.variants.family_variant import FamilyAllele


@pytest.fixture()
def denovo_broken_pedigrees(
    tmp_path: pathlib.Path,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
) -> GenotypeData:
    ped_path = setup_pedigree(
        tmp_path / "pedigree_data" / "in.ped",
        """
            familyId personId dadId	 momId	sex status role
            f1       p1       0      0      2   2      prb
            f1       s1       0      0      2   1      sib
            f2       p2       0      0      2   2      prb
        """,
    )
    denovo_path = setup_denovo(
        tmp_path / "denovo_dae_data" / "in.tsv",
        """
          familyId  location  variant    bestState
          f1        foo:10    sub(A->G)  1||1/1||0
          f1        foo:11    sub(T->A)  1||2/1||0
          f1        bar:10    sub(G->A)  2||1/0||1
          f2        bar:11    sub(G->A)  1/1
          f2        bar:12    sub(G->A)  1/1
        """,
    )
    genotype_storage = genotype_storage_factory(
        tmp_path / "denovo_broken_pedigrees" / "genotype_storage")
    gpf = foobar_gpf(tmp_path, genotype_storage)
    return denovo_study(
        tmp_path, "denovo_broken_pedigrees",
        ped_path, [denovo_path],
        gpf)


def test_query_denovo_variants(denovo_broken_pedigrees: GenotypeData) -> None:
    vs = list(denovo_broken_pedigrees.query_variants())
    assert len(vs) == 5
    for v in vs:
        for aa in v.alt_alleles:
            fa = cast(FamilyAllele, aa)
            assert Inheritance.denovo in fa.inheritance_in_members
