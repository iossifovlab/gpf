# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
import pathlib

import pytest
from box import Box

from dae.testing import setup_pedigree

from dae.pedigrees.loader import FamiliesLoader
from dae.pedigrees.family import FamiliesData
from dae.person_sets import PersonSetCollection


@pytest.fixture
def families_fixture(tmp_path: pathlib.Path) -> FamiliesData:

    ped_path = setup_pedigree(
        tmp_path / "test_pedigree" / "ped.ped",
        textwrap.dedent("""
            familyId personId dadId	 momId	sex status role
            f1       mom1     0      0      2   1      mom
            f1       dad1     0      0      1   1      dad
            f1       prb1     dad1   mom1   1   2      prb
            f1       sib1     dad1   mom1   2   2      sib
            f1       sib2     dad1   mom1   2   2      sib
            f2       grmom2   0      0      2   1      maternal_grandmother
            f2       grdad2   0      0      1   1      maternal_grandfather
            f2       mom2     grdad2 grmom2 2   1      mom
            f2       dad2     0      0      1   1      dad
            f2       prb2     dad2   mom2   1   2      prb
            f2       sib2_3   dad2   mom2   2   2      sib
        """))
    families = FamiliesLoader(ped_path).load()
    assert families is not None
    return families


def test_create_person_set_collection(
    families_fixture: FamiliesData,
    tmp_path: pathlib.Path
) -> None:
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
    person_set_collection = PersonSetCollection.from_families(
        Box(status_config),
        families_fixture
    )
    assert person_set_collection is not None

    assert len(person_set_collection.person_sets) == 2
    assert "unknown" not in person_set_collection.person_sets
