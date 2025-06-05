# pylint: disable=W0621,C0114,C0116,W0212,W0613
import io
import textwrap
from collections.abc import Callable

import pytest

from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.testing import convert_to_tab_separated
from dae.variants_loaders.cnv.flexible_cnv_loader import (
    _configure_cnv_best_state,
    _configure_cnv_location,
)


@pytest.fixture
def families() -> FamiliesData:
    ped_content = io.StringIO(convert_to_tab_separated(textwrap.dedent(
        """
            familyId personId dadId	 momId	sex status role
            f1       f1.m     0      0      2   1      mom
            f1       f1.d     0      0      1   1      dad
            f1       f1.p1    f1.d   f1.m   1   2      prb
            f1       f1.s2    f1.d   f1.m   2   1      sib
            f2       f2.m     0      0      2   1      mom
            f2       f2.d     0      0      1   1      dad
            f2       f2.p1    f2.d   f2.m   2   2      prb
        """)))
    families = FamiliesLoader(ped_content).load()
    assert families is not None
    return families


def test_configure_cnv_loader_vcf_like_pos() -> None:
    header = ["person_id", "Chr", "Start", "End", "variant", "extra"]
    transformers: list[Callable] = []

    _configure_cnv_location(
        header, transformers,
        cnv_chrom="Chr",
        cnv_start="Start",
        cnv_end="End",
    )

    assert header == [
        "person_id", "chrom", "pos", "pos_end", "variant", "extra"]


def test_configure_cnv_loader_vcf_like_pos_missmatch() -> None:

    header = ["person_id", "Chr", "Start", "End", "variant", "extra"]
    transformers: list[Callable] = []

    with pytest.raises(ValueError, match="'Chrom' is not in list"):
        _configure_cnv_location(
            header, transformers,
            cnv_chrom="Chrom",
            cnv_start="Start",
            cnv_end="End",
        )


def test_configure_cnv_loader_location() -> None:
    header = ["person_id", "location", "variant", "extra"]
    transformers: list[Callable] = []
    _configure_cnv_location(header, transformers)
    assert header == [
        "person_id", "location", "variant", "extra"]


def test_configure_cnv_loader_location_mismatch() -> None:
    header = ["person_id", "location", "variant", "extra"]
    transformers: list[Callable] = []
    with pytest.raises(ValueError, match="'Location' is not in list"):
        _configure_cnv_location(
            header, transformers, cnv_location="Location")


def test_configure_cnv_loader_dae_best_state(
    families: FamiliesData,
    acgt_genome_19: ReferenceGenome,
) -> None:

    header = ["familyId", "location", "variant", "bestState", "extra"]
    transformers: list[Callable] = []

    _configure_cnv_best_state(
        header, transformers,
        families,
        genome=acgt_genome_19,
        cnv_family_id="familyId",
        cnv_best_state="bestState",
    )

    assert header == [
        "family_id", "location", "variant", "best_state", "extra"]


def test_configure_cnv_loader_person_id(
    families: FamiliesData,
    acgt_genome_19: ReferenceGenome,
) -> None:

    header = ["personId", "location", "variant", "extra"]
    transformers: list[Callable] = []

    _configure_cnv_best_state(
        header, transformers,
        families,
        genome=acgt_genome_19,
        cnv_person_id="personId",
    )

    assert header == [
        "person_id", "location", "variant", "extra"]


def test_configure_cnv_loader_best_state_person_id_not_found(
    families: FamiliesData,
    acgt_genome_19: ReferenceGenome,
) -> None:

    header = ["personId", "location", "variant", "extra"]
    transformers: list[Callable] = []

    with pytest.raises(ValueError, match="'person_id' is not in list"):
        _configure_cnv_best_state(
            header, transformers,
            families,
            genome=acgt_genome_19,
            cnv_person_id="person_id",
        )


def test_configure_cnv_loader_best_state_best_state_not_found(
    families: FamiliesData,
    acgt_genome_19: ReferenceGenome,
) -> None:

    header = ["familyId", "location", "variant", "bestState", "extra"]
    transformers: list[Callable] = []

    with pytest.raises(ValueError, match="'best_state' is not in list"):
        _configure_cnv_best_state(
            header, transformers,
            families,
            genome=acgt_genome_19,
            cnv_family_id="familyId",
            cnv_best_state="best_state",
        )


def test_configure_cnv_loader_best_state_family_id_not_found(
    families: FamiliesData,
    acgt_genome_19: ReferenceGenome,
) -> None:

    header = ["familyId", "location", "variant", "bestState", "extra"]
    transformers: list[Callable] = []

    with pytest.raises(ValueError, match="'family_id' is not in list"):
        _configure_cnv_best_state(
            header, transformers,
            families,
            genome=acgt_genome_19,
            cnv_family_id="family_id",
            cnv_best_state="bestState",
        )
