# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from typing import Optional

import pytest

from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing import cnv_study, setup_denovo, setup_pedigree
from dae.testing.alla_import import alla_gpf
from dae.utils.regions import Region


@pytest.fixture(scope="module")
def imported_study(
        tmp_path_factory: pytest.TempPathFactory,
        genotype_storage: GenotypeStorage) -> GenotypeData:
    root_path = tmp_path_factory.mktemp(
        f"cnv_variants_{genotype_storage.storage_id}")
    gpf_instance = alla_gpf(root_path, genotype_storage)
    ped_path = setup_pedigree(
        root_path / "cnv_data" / "in.ped",
        """
        familyId  personId  dadId  momId  sex  status  role
        f1        f1.mo     0      0      2    1       mom
        f1        f1.fa     0      0      1    1       dad
        f1        f1.p1     f1.fa  f1.mo  1    2       prb
        f1        f1.s1     f1.fa  f1.mo  2    1       sib
        f2        f2.mo     0      0      2    1       mom
        f2        f2.fa     0      0      1    1       dad
        f2        f2.p1     f2.fa  f2.mo  1    2       prb
        """)
    cnv_path = setup_denovo(
        root_path / "cnv_data" / "in.tsv",
        """
family_id location    variant  best_state
f1        chrA:1-20   CNV+     2||2||2||3
f1        chrA:31-50  CNV-     2||2||2||1
f2        chrA:51-70  CNV+     2||2||3
f2        chrA:81-100 CNV-     2||2||1
        """)

    study = cnv_study(
        root_path,
        "cnv_variants", pathlib.Path(ped_path),
        [pathlib.Path(cnv_path)],
        gpf_instance)
    return study


@pytest.mark.parametrize(
    "pos_begin, pos_end, variant_type, count",
    [
        (None, None, None, 4),
        (None, None, "cnv+", 2),
        (None, None, "cnv-", 2),
        (None, None, "cnv- or cnv+", 4),
        (1, 10, None, 1),
        (1, 10, "cnv+", 1),
        (1, 10, "cnv-", 0),
        (10, 40, None, 2),
        (10, 40, "cnv+", 1),
        (10, 40, "cnv-", 1),
        (10, 60, None, 3),
        (10, 60, "cnv+", 2),
        (10, 60, "cnv-", 1),
        (10, 60, "cnv- or cnv+", 3),
        (40, 60, None, 2),
        (40, 90, None, 3),
        (40, 81, None, 3),
    ],
)
def test_query_cnv_variants(
        imported_study: GenotypeData,
        pos_begin: Optional[int],
        pos_end: Optional[int],
        variant_type: Optional[str],
        count: int) -> None:
    if pos_begin is not None and pos_end is not None:
        regions = [Region("chrA", pos_begin, pos_end)]
    else:
        regions = None
    vs = list(imported_study.query_variants(
        regions=regions,
        variant_type=variant_type))
    assert len(vs) == count
