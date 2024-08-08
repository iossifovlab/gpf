# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap
from typing import Any

import pytest

from dae.studies.study import GenotypeData
from dae.testing import foobar_gpf, setup_dae_transmitted, setup_pedigree
from dae.testing.import_helpers import dae_study
from dae.utils.regions import Region
from dae.utils.variant_utils import str2lists


@pytest.fixture()
def study(tmp_path: pathlib.Path) -> GenotypeData:
    gpf_instance = foobar_gpf(tmp_path)
    ped_path = setup_pedigree(
        tmp_path / "study_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     2   2      prb
        f1       s1       d1     m1     2   1      sib
        f2       m2       0      0      2   1      mom
        f2       d2       0      0      1   1      dad
        f2       p2       d2     m2     2   2      prb
    """)
    summary_path, _ = setup_dae_transmitted(
        tmp_path / "transmitted_data" / "in.tsv",
        textwrap.dedent("""
chr position variant   familyData all.nParCalled all.prcntParCalled all.nAltAlls all.altFreq
foo 10       sub(T->G) TOOMANY    1400           27.03              13           0.49
bar 10       sub(T->C) TOOMANY    1460           29.54              1            0.03
bar 11       sub(A->G) TOOMANY    300            6.07               588          98.00
        """),  # noqa
        textwrap.dedent("""
chr position variant   familyData
foo 10       sub(T->G) f1:0000/2222:0||0||0||0/71||38||36||29/0||0||0||0
bar 10       sub(T->C) f1:0110/2112:0||63||67||0/99||56||57||98/0||0||0||0
bar 11       sub(A->G) f1:1121/1101:38||4||83||25/16||23||0||16/0||0||0||0;f2:211/011:13||5||5/0||13||17/0||0||0
        """)  # noqa
    )
    return dae_study(
        tmp_path,
        "transmitted_study", ped_path, [summary_path],
        gpf_instance)


@pytest.mark.parametrize("params, count, expected", [
    ({"family_ids": ["f1"], "regions": [Region("foo", 10, 10)]}, 1,
     "0 0 0 0/71 38 36 29/0 0 0 0"),
    ({"family_ids": ["f1"], "regions": [Region("bar", 10, 10)]}, 1,
     "0 63 67 0/99 56 57 98/0 0 0 0"),
    ({"family_ids": ["f1"], "regions": [Region("bar", 11, 11)]}, 1,
     "38 4 83 25/16 23 0 16/0 0 0 0"),
    ({"family_ids": ["f2"], "regions": [Region("bar", 11, 11)]}, 1,
     "13 5 5/0 13 17/0 0 0"),
])
def test_dae_read_counts_serialization(
    params: dict[str, Any],
    count: int,
    expected: str,
    study: GenotypeData,
) -> None:
    assert study is not None

    vs = list(study.query_variants(**params))
    assert len(vs) == count

    for v in vs:
        for fa in v.family_alt_alleles:
            read_counts = fa.get_attribute("read_counts")
            assert read_counts is not None
            assert read_counts == str2lists(expected, col_sep=" ", row_sep="/")
