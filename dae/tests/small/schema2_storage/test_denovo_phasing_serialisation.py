# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from typing import Any, cast

import pytest
from dae.genomic_resources.testing import setup_denovo, setup_pedigree
from dae.studies.study import GenotypeData
from dae.testing.foobar_import import foobar_gpf
from dae.testing.import_helpers import denovo_study
from dae.utils.regions import Region


@pytest.fixture
def study(tmp_path: pathlib.Path) -> GenotypeData:
    root_path = tmp_path
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
        f2       p2       d2     m2     1   2      prb
        """)
    denovo_path = setup_denovo(
        root_path / "trios2_data" / "in.tsv",
        """
          chrom pos  ref  alt  person_id fromParent
          foo   10   A    G    p1,s1     mom
          foo   10   A    G    p2        dad
          bar   10   G    A    s1        mom
          bar   11   G    A    p2        mom
        """,
    )

    return denovo_study(
        root_path,
        "trios2", ped_path, [denovo_path],
        gpf_instance=gpf_instance)


@pytest.mark.parametrize("params, count, phasing", [
    ({"family_ids": ["f1"]}, 2, "mom"),
    ({"family_ids": ["f2"], "regions": [Region("foo", 10, 10)]}, 1, "dad"),
    ({"family_ids": ["f2"], "regions": [Region("bar", 1, 100)]}, 1, "mom"),
])
def test_phasing_serialization(
    params: dict[str, Any],
    count: int,
    phasing: str,
    study: GenotypeData,
) -> None:
    assert study is not None

    vs = list(study.query_variants(**params))
    assert len(vs) == count

    for v in vs:
        for aa in v.family_alt_alleles:
            from_parent = cast(
                str | None, aa.family_attributes.get("fromParent"))
            assert from_parent is not None
            assert from_parent == phasing
