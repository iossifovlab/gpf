# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from collections.abc import Callable
from typing import cast

import pytest
from dae.genomic_resources.testing import (
    setup_denovo,
    setup_pedigree,
)
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing.foobar_import import foobar_gpf
from dae.testing.import_helpers import denovo_study
from dae.variants.attributes import Inheritance
from dae.variants.family_variant import FamilyAllele


@pytest.fixture
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
          chrom  pos  ref  alt  person_id
          foo    10   A    G    p1,s1
          foo    11   T    A    p1
          bar    10   G    A    s1
          bar    11   G    A    p2
          bar    12   G    A    p2
        """,
    )
    genotype_storage = genotype_storage_factory(
        tmp_path / "denovo_broken_pedigrees" / "genotype_storage")
    gpf = foobar_gpf(tmp_path, genotype_storage)
    return denovo_study(
        tmp_path, "test_denovo_broken_pedigrees",
        ped_path, [denovo_path],
        gpf_instance=gpf)


def test_query_denovo_variants(denovo_broken_pedigrees: GenotypeData) -> None:
    vs = list(denovo_broken_pedigrees.query_variants())
    assert len(vs) == 5
    for v in vs:
        for aa in v.alt_alleles:
            fa = cast(FamilyAllele, aa)
            assert Inheritance.denovo in fa.inheritance_in_members
