# pylint: disable=W0621,C0114,C0116,W0212,W0613
import logging
import pathlib
from types import SimpleNamespace
from typing import cast

import pytest
from gain.genomic_resources.testing import setup_pedigree

from gpf.pedigrees.families_data import FamiliesData
from gpf.pedigrees.family import Person
from gpf.pedigrees.loader import FamiliesLoader
from gpf.variants_loaders.vcf.loader import SingleVcfLoader, VcfLoader


@pytest.fixture
def trio_families(tmp_path: pathlib.Path) -> FamiliesData:
    ped_path = setup_pedigree(tmp_path / "in.ped", """
    familyId	personId	dadId	momId	sex	status	role
    f1	        f1.mom  	0   	0	    2	1	    mom
    f1	        f1.dad  	0	    0	    1	1	    dad
    f1	        f1.p1   	f1.dad	f1.mom	1	2	    prb
    """)
    return FamiliesLoader(str(ped_path)).load()


def _loader_with(*families: FamiliesData) -> VcfLoader:
    loader = VcfLoader.__new__(VcfLoader)
    loader.vcf_loaders = [
        cast(SingleVcfLoader, SimpleNamespace(families=fams))
        for fams in families
    ]
    return loader


def _person(families: FamiliesData, person_id: str) -> Person:
    return families.persons["f1", person_id]


def test_intersection_without_loaders_fails() -> None:
    loader = VcfLoader.__new__(VcfLoader)
    loader.vcf_loaders = None

    with pytest.raises(AssertionError):
        loader._families_intersection()


def test_intersection_single_loader_returns_its_families(
    trio_families: FamiliesData,
    caplog: pytest.LogCaptureFixture,
) -> None:
    loader = _loader_with(trio_families)

    with caplog.at_level(logging.WARNING):
        result = loader._families_intersection()

    assert result is trio_families
    assert caplog.text == ""


def test_intersection_marks_persons_not_sequenced_in_any_loader(
    trio_families: FamiliesData,
    caplog: pytest.LogCaptureFixture,
) -> None:
    other = trio_families.copy()
    _person(other, "f1.dad").set_attr("not_sequenced", value=True)
    loader = _loader_with(trio_families, other)

    with caplog.at_level(logging.WARNING):
        result = loader._families_intersection()

    assert result is trio_families
    assert _person(result, "f1.dad").not_sequenced
    assert not _person(result, "f1.mom").not_sequenced
    assert not _person(result, "f1.p1").not_sequenced
    assert "families intersection run..." in caplog.text
    assert "person f1.dad is marked as 'not_sequenced'" in caplog.text


def test_intersection_redefines_families_after_merge(
    trio_families: FamiliesData,
) -> None:
    assert ("f1", "f1.dad") in trio_families.real_persons
    other = trio_families.copy()
    _person(other, "f1.dad").set_attr("not_sequenced", value=True)
    loader = _loader_with(trio_families, other)

    result = loader._families_intersection()

    assert ("f1", "f1.dad") not in result.real_persons
    assert set(result.real_persons) == {("f1", "f1.mom"), ("f1", "f1.p1")}


def test_intersection_single_loader_skips_redefine(
    trio_families: FamiliesData,
) -> None:
    assert ("f1", "f1.dad") in trio_families.real_persons
    _person(trio_families, "f1.dad").set_attr("not_sequenced", value=True)
    loader = _loader_with(trio_families)

    result = loader._families_intersection()

    assert ("f1", "f1.dad") in result.real_persons


def test_intersection_makes_all_loaders_share_one_families(
    trio_families: FamiliesData,
) -> None:
    loader = _loader_with(trio_families, trio_families.copy())

    result = loader._families_intersection()

    assert loader.vcf_loaders is not None
    assert all(
        vcf_loader.families is result
        for vcf_loader in loader.vcf_loaders)


def test_intersection_sets_attribute_for_generated_person_of_other_loader(
    trio_families: FamiliesData,
) -> None:
    other = trio_families.copy()
    _person(other, "f1.mom").set_attr("generated", value=True)
    loader = _loader_with(trio_families, other)

    result = loader._families_intersection()

    mom = _person(result, "f1.mom")
    assert mom.get_attr("not_sequenced") is True
    assert not mom.generated


def test_intersection_compares_first_loader_with_itself(
    trio_families: FamiliesData,
) -> None:
    other = trio_families.copy()
    _person(trio_families, "f1.mom").set_attr("generated", value=True)
    loader = _loader_with(trio_families, other)

    result = loader._families_intersection()

    assert _person(result, "f1.mom").get_attr("not_sequenced") is True
    assert not _person(result, "f1.dad").has_attr("not_sequenced")


def test_intersection_fails_on_different_person_counts(
    trio_families: FamiliesData,
    tmp_path: pathlib.Path,
) -> None:
    ped_path = setup_pedigree(tmp_path / "other.ped", """
    familyId	personId	dadId	momId	sex	status	role
    f1	        f1.mom  	0   	0	    2	1	    mom
    f1	        f1.dad  	0	    0	    1	1	    dad
    f1	        f1.p1   	f1.dad	f1.mom	1	2	    prb
    f1	        f1.s1   	f1.dad	f1.mom	2	1	    sib
    """)
    other = FamiliesLoader(str(ped_path)).load()
    loader = _loader_with(trio_families, other)

    with pytest.raises(AssertionError):
        loader._families_intersection()
