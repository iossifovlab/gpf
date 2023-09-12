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
familyId personId dadId	 momId	sex status role                 generated
f1       grmom1   0      0      2   0      maternal_grandmother True
f1       grdad1   0      0      1   0      maternal_grandfather True
f1       mom1     0      0      2   1      mom                  False
f1       dad1     0      0      1   1      dad                  False
f1       prb1     dad1   mom1   1   2      prb                  False
f1       sib1     dad1   mom1   2   2      sib                  False
f1       sib2     dad1   mom1   2   2      sib                  False
f2       grmom2   0      0      2   0      maternal_grandmother True
f2       grdad2   0      0      1   1      maternal_grandfather False
f2       mom2     grdad2 grmom2 2   1      mom                  False
f2       dad2     0      0      1   1      dad                  False
f2       prb2     dad2   mom2   1   2      prb                  False
f2       sib2_3   dad2   mom2   2   2      sib                  False
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
