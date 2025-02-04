# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

import pysam
import pytest

from dae.genomic_resources.repository_factory import (
    GenomicResourceRepo,
)
from dae.genomic_resources.testing import (
    setup_dae_transmitted,
    setup_pedigree,
)
from dae.tools.dae2vcf import main as dae2vcf_main


@pytest.fixture(scope="module")
def dae_pedigree(
    tmp_path_factory: pytest.TempPathFactory,
) -> pathlib.Path:
    root_path = tmp_path_factory.mktemp("test_dae2vcf")
    return setup_pedigree(root_path / "ped_data" / "in.ped", """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     2   2      prb
        f1       s1       d1     m1     2   1      sib
        f2       m2       0      0      2   1      mom
        f2       d2       0      0      1   1      dad
        f2       p2       d2     m2     2   2      prb
    """)


@pytest.fixture(scope="session")
def dae_summary(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    root_path = tmp_path_factory.mktemp("test_dae2vcf")
    summary_data, _toomany_data = setup_dae_transmitted(
        root_path,
        textwrap.dedent("""
chr  position variant   familyData all.nParCalled all.prcntParCalled all.nAltAlls all.altFreq
chr1 1        sub(T->G) TOOMANY    1400           27.03              13           0.49
chr1 5        sub(T->C) TOOMANY    1460           29.54              1            0.03
chr1 12       sub(T->G) TOOMANY    300            6.07               588          98.00
        """),  # noqa
        textwrap.dedent("""
chr  position variant   familyData
chr1 1        sub(T->G) f1:0000/2222:0||0||0||0/71||38||36||29/0||0||0||0
chr1 5        sub(T->C) f1:0110/2112:0||63||67||0/99||56||57||98/0||0||0||0
chr1 12       sub(A->G) f1:1121/1101:38||4||83||25/16||23||0||16/0||0||0||0;f2:211/011:13||5||5/0||13||17/0||0||0
        """)  # noqa
    )
    return summary_data


def test_dae2vcf_simple(
    dae_pedigree: pathlib.Path,
    dae_summary: pathlib.Path,
    tmp_path: pathlib.Path,
    t4c8_grr: GenomicResourceRepo,
) -> None:
    # When:
    dae2vcf_main(
        [
            str(dae_pedigree),
            str(dae_summary),
            "--genome", "t4c8_genome",
            "--output", str(tmp_path / "out.vcf"),
        ],
        grr=t4c8_grr,
    )

    # Then:
    assert (tmp_path / "out.vcf").exists()

    vcf = pysam.VariantFile(str(tmp_path / "out.vcf"))

    variants = list(vcf.fetch())
    assert len(variants) == 3
    for variant in variants:
        assert variant.alts is not None
        assert variant.id == \
            f"{variant.chrom}_{variant.pos}_{variant.ref}_{variant.alts[0]}"
