# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
import pathlib
from typing import Any

import pytest
from box import Box

from dae.testing import setup_pedigree

from dae.pedigrees.loader import FamiliesLoader
from dae.person_sets import PersonSetCollection


@pytest.fixture
def status_config() -> dict[str, Any]:
    return {
        "id": "affected_status",
        "name": "Affected Status",
        "sources": [
            {
                "from": "pedigree",
                "source": "status"
            }
        ],
        "domain": [
            {
                "id": "affected",
                "name": "Affected",
                "values": ["affected"],
                "color": "#aabbcc"
            },
            {
                "id": "unaffected",
                "name": "Unaffected",
                "values": ["unaffected"],
                "color": "#ffffff"
            }
        ],
        "default": {
            "id": "unknown",
            "name": "Unknown",
            "color": "#aaaaaa"
        }
    }


def test_create_person_set_collection_with_missing_persons(
    tmp_path: pathlib.Path,
    status_config: dict[str, Any]
) -> None:
    families = FamiliesLoader(
        setup_pedigree(
            tmp_path / "test_pedigree" / "ped.ped",
            textwrap.dedent("""
familyId personId dadId	 momId	sex status role  generated  missing
f1       prb1     0      0      1   2      prb   False      False
f1       sib1     0      0      2   1      sib   False      False
f1       sib3     0      0      2   0      sib   True       False
f1       sib4     0      0      2   0      sib   False      True
            """))
    ).load()

    person_set_collection = PersonSetCollection.from_families(
        Box(status_config),
        families
    )
    assert person_set_collection is not None

    assert len(person_set_collection.person_sets) == 2
    assert "unknown" not in person_set_collection.person_sets


def test_create_person_set_collection_with_unspecified_status(
    tmp_path: pathlib.Path,
    status_config: dict[str, Any]
) -> None:
    families = FamiliesLoader(
        setup_pedigree(
            tmp_path / "test_pedigree" / "ped.ped",
            textwrap.dedent("""
familyId personId dadId	 momId	sex status role  generated  missing
f1       prb1     0      0      1   2      prb   False      False
f1       sib1     0      0      2   1      sib   False      False
f1       sib3     0      0      2   0      sib   False      False
f1       sib4     0      0      2   0      sib   False      True
            """))
    ).load()

    person_set_collection = PersonSetCollection.from_families(
        Box(status_config),
        families
    )
    assert person_set_collection is not None

    assert len(person_set_collection.person_sets) == 3
    assert "unknown" in person_set_collection.person_sets


def test_create_person_set_collection_only_affected(
    tmp_path: pathlib.Path,
    status_config: dict[str, Any]
) -> None:
    families = FamiliesLoader(
        setup_pedigree(
            tmp_path / "test_pedigree" / "ped.ped",
            textwrap.dedent("""
familyId personId dadId	 momId	sex status role  generated  missing
f1       prb1     0      0      1   2      prb   False      False
f1       sib1     0      0      2   2      sib   False      False
            """))
    ).load()

    person_set_collection = PersonSetCollection.from_families(
        Box(status_config),
        families
    )
    assert person_set_collection is not None

    assert len(person_set_collection.person_sets) == 1
    assert "unknown" not in person_set_collection.person_sets
    assert "unaffected" not in person_set_collection.person_sets
    assert "affected" in person_set_collection.person_sets


def test_create_person_set_collection_only_unaffected(
    tmp_path: pathlib.Path,
    status_config: dict[str, Any]
) -> None:
    families = FamiliesLoader(
        setup_pedigree(
            tmp_path / "test_pedigree" / "ped.ped",
            textwrap.dedent("""
familyId personId dadId	 momId	sex status role  generated  missing
f1       sib1     0      0      2   1      sib   False      False
f1       sib3     0      0      2   1      sib   False      False
f1       sib4     0      0      2   0      sib   False      True
            """))
    ).load()

    person_set_collection = PersonSetCollection.from_families(
        Box(status_config),
        families
    )
    assert person_set_collection is not None

    assert len(person_set_collection.person_sets) == 1
    assert "unknown" not in person_set_collection.person_sets
    assert "affected" not in person_set_collection.person_sets
    assert "unaffected" in person_set_collection.person_sets


def test_person_set_collection_only_default(
    tmp_path: pathlib.Path,
) -> None:
    families = FamiliesLoader(
        setup_pedigree(
            tmp_path / "test_pedigree" / "ped.ped",
            textwrap.dedent("""
familyId personId dadId	 momId	sex status role  generated  missing
f1       sib1     0      0      2   1      sib   False      False
f1       sib3     0      0      2   1      sib   False      False
f1       sib4     0      0      2   0      sib   False      True
            """))
    ).load()

    status_config = {
        "id": "affected_status",
        "name": "Affected Status",
        "sources": [
            {
                "from": "pedigree",
                "source": "status"
            }
        ],
        "domain": [
        ],
        "default": {
            "id": "unknown",
            "name": "Unknown",
            "color": "#aaaaaa"
        }
    }
    person_set_collection = PersonSetCollection.from_families(
        Box(status_config),
        families
    )
    assert person_set_collection is not None

    assert len(person_set_collection.person_sets) == 1
    assert "unknown" in person_set_collection.person_sets
    assert "affected" not in person_set_collection.person_sets
    assert "unaffected" not in person_set_collection.person_sets

    person_set = person_set_collection.person_sets["unknown"]
    assert len(person_set) == 2


def test_person_set_collection_only_unaffected(
    tmp_path: pathlib.Path,
) -> None:
    families = FamiliesLoader(
        setup_pedigree(
            tmp_path / "test_pedigree" / "ped.ped",
            textwrap.dedent("""
familyId personId dadId	 momId	sex status role  generated  missing
f1       sib1     0      0      2   1      sib   False      False
f1       sib3     0      0      2   1      sib   False      False
f1       sib4     0      0      2   0      sib   False      True
            """))
    ).load()

    status_config = {
        "id": "affected_status",
        "name": "Affected Status",
        "sources": [
            {
                "from": "pedigree",
                "source": "status"
            }
        ],
        "domain": [
            {
                "id": "unaffected",
                "name": "Unaffected",
                "values": ["unaffected"],
                "color": "#ffffff"
            }
        ],
        "default": {
            "id": "unknown",
            "name": "Unknown",
            "color": "#aaaaaa"
        }
    }
    person_set_collection = PersonSetCollection.from_families(
        Box(status_config),
        families
    )
    assert person_set_collection is not None

    assert len(person_set_collection.person_sets) == 1
    assert "unknown" not in person_set_collection.person_sets
    assert "affected" not in person_set_collection.person_sets
    assert "unaffected" in person_set_collection.person_sets

    person_set = person_set_collection.person_sets["unaffected"]
    assert len(person_set) == 2


def test_person_set_collection_unaffected_and_default(
    tmp_path: pathlib.Path,
) -> None:
    families = FamiliesLoader(
        setup_pedigree(
            tmp_path / "test_pedigree" / "ped.ped",
            textwrap.dedent("""
familyId personId dadId	 momId	sex status role  generated  missing
f1       prb1     0      0      1   2      prb   False      False
f1       sib1     0      0      2   1      sib   False      False
f1       sib3     0      0      2   1      sib   False      False
f1       sib4     0      0      2   1      sib   False      False
            """))
    ).load()

    status_config = {
        "id": "affected_status",
        "name": "Affected Status",
        "sources": [
            {
                "from": "pedigree",
                "source": "status"
            }
        ],
        "domain": [
            {
                "id": "unaffected",
                "name": "Unaffected",
                "values": ["unaffected"],
                "color": "#ffffff"
            }
        ],
        "default": {
            "id": "unknown",
            "name": "Unknown",
            "color": "#aaaaaa"
        }
    }
    person_set_collection = PersonSetCollection.from_families(
        Box(status_config),
        families
    )
    assert person_set_collection is not None

    assert len(person_set_collection.person_sets) == 2
    assert "unknown" in person_set_collection.person_sets
    assert "unaffected" in person_set_collection.person_sets
    assert "affected" not in person_set_collection.person_sets

    person_set = person_set_collection.person_sets["unaffected"]
    assert len(person_set) == 3

    person_set = person_set_collection.person_sets["unknown"]
    assert len(person_set) == 1
