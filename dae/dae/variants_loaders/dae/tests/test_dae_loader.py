# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
from pathlib import Path

import numpy as np
import pytest

from dae.genomic_resources.testing import setup_dae_transmitted
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.testing import build_families_data
from dae.testing import foobar_gpf
from dae.utils.regions import Region
from dae.utils.variant_utils import mat2str, str2mat
from dae.variants_loaders.dae.loader import DaeTransmittedLoader


@pytest.fixture(scope="session")
def gpf_instance(tmp_path_factory: pytest.TempPathFactory) -> GPFInstance:
    root_path = tmp_path_factory.mktemp("foobar_gpf_instance")
    return foobar_gpf(root_path)


@pytest.fixture(scope="session")
def families_data() -> FamiliesData:
    return build_families_data("""
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
def summary_data(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("dae_data")
    summary_data, _toomany_data = setup_dae_transmitted(
        root_path,
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
    return summary_data


@pytest.fixture(scope="session")
def dae_transmitted(
    gpf_instance: GPFInstance,
    families_data: FamiliesData,
    summary_data: Path,
) -> DaeTransmittedLoader:
    return DaeTransmittedLoader(
        families_data,
        str(summary_data),
        genome=gpf_instance.reference_genome,
        regions=None,
    )


def test_dae_transmitted_loader_simple(
    dae_transmitted: DaeTransmittedLoader,
) -> None:
    read_counts = None
    for fv in dae_transmitted.family_variants_iterator():
        assert fv.gt is not None
        print(fv, mat2str(fv.best_state), mat2str(fv.gt))
        for fa in fv.alt_alleles:
            read_counts = fa.get_attribute("read_counts")
            assert read_counts is not None
    assert np.all(
        read_counts == str2mat(
            "13 5 5/0 13 17/0 0 0", col_sep=" ", row_sep="/"))


def test_chromosomes_have_adjusted_chrom(
    gpf_instance: GPFInstance, families_data: FamiliesData, summary_data: Path,
) -> None:
    variants_loader = DaeTransmittedLoader(
        families_data,
        str(summary_data),
        genome=gpf_instance.reference_genome,
        params={"add_chrom_prefix": "chr"},
        regions=None,
    )

    assert variants_loader.chromosomes == ["chrfoo", "chrbar"]


def test_variants_have_adjusted_chrom(
    gpf_instance: GPFInstance, families_data: FamiliesData, summary_data: Path,
) -> None:
    variants_loader = DaeTransmittedLoader(
        families_data,
        str(summary_data),
        genome=gpf_instance.reference_genome,
        params={"add_chrom_prefix": "chr"},
        regions=None,
    )

    variants = list(variants_loader.full_variants_iterator())
    assert len(variants) > 0
    for summary_variant, _ in variants:
        assert summary_variant.chromosome.startswith("chr")


def test_reset_regions_with_adjusted_chrom(
    gpf_instance: GPFInstance, families_data: FamiliesData, summary_data: Path,
) -> None:
    variants_loader = DaeTransmittedLoader(
        families_data,
        str(summary_data),
        genome=gpf_instance.reference_genome,
        params={"add_chrom_prefix": "chr"},
        regions=None,
    )

    regions = [Region.from_str("chrbar:10-11")]

    variants_loader.reset_regions(regions)

    variants = list(variants_loader.full_variants_iterator())
    assert len(variants) == 2
    unique_chroms = np.unique([sv.chromosome for sv, _ in variants])
    assert unique_chroms is not None
    assert (unique_chroms == ["chrbar"]).all()


def test_end_position(
    gpf_instance: GPFInstance, families_data: FamiliesData, summary_data: Path,
) -> None:
    variants_loader = DaeTransmittedLoader(
        families_data,
        str(summary_data),
        genome=gpf_instance.reference_genome,
        params={"add_chrom_prefix": "chr"},
        regions=None,
    )
    variants = list(variants_loader.full_variants_iterator())
    for sv, _fvs in variants:
        assert sv.position is not None
        assert sv.end_position is not None
        assert sv.position == sv.end_position
