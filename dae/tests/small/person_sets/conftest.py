# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

import pytest
import yaml
from dae.genomic_resources.testing import setup_pedigree
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.person_sets import (
    PersonSetCollection,
    parse_person_set_collection_config,
)


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
            f2       grmom2   0      0      2   0      maternal_grandmother
            f2       grdad2   0      0      1   0      maternal_grandfather
            f2       mom2     grdad2 grmom2 2   1      mom
            f2       dad2     0      0      1   1      dad
            f2       prb2     dad2   mom2   1   2      prb
            f2       sib2_3   dad2   mom2   2   2      sib
        """))
    families = FamiliesLoader(ped_path).load()
    assert families is not None
    return families


@pytest.fixture
def phenotype_psc(
    families_fixture: FamiliesData,
) -> PersonSetCollection:
    content = textwrap.dedent(
        """
          id: phenotype
          name: Phenotype
          sources:
          - from: pedigree
            source: status
          domain:
          - id: autism
            name: autism
            values:
            - affected
            color: '#ff2121'
          - id: unaffected
            name: unaffected
            values:
            - unaffected
            color: '#ffffff'
          - id: unspecified
            name: unspecified
            values:
            - unspecified
            color: '#aaaaaa'
          default:
            id: unknown
            name: unknown
            color: '#cccccc'
        """)
    config = parse_person_set_collection_config(yaml.safe_load(content))
    return PersonSetCollection.from_families(config, families_fixture)


@pytest.fixture
def status_psc(
    families_fixture: FamiliesData,
) -> PersonSetCollection:
    content = textwrap.dedent(
        """
          id: status
          name: Affected Status
          sources:
          - from: pedigree
            source: status
          domain:
          - id: affected
            name: affected
            values:
            - affected
            color: '#ff2121'
          - id: unaffected
            name: unaffected
            values:
            - unaffected
            color: '#ffffff'
          - id: unspecified
            name: unspecified
            values:
            - unspecified
            color: '#aaaaaa'
          default:
            id: unknown
            name: unknown
            color: '#cccccc'
        """)
    config = parse_person_set_collection_config(yaml.safe_load(content))
    return PersonSetCollection.from_families(config, families_fixture)


@pytest.fixture
def status_sex_psc(
    families_fixture: FamiliesData,
) -> PersonSetCollection:
    content = textwrap.dedent(
        """
          id: status_sex
          name: Affected Status and Sex
          sources:
          - from: pedigree
            source: status
          - from: pedigree
            source: sex
          domain:
          - id: affected_male
            name: affected male
            values:
            - affected
            - M
            color: '#ff2121'
          - id: affected_female
            name: affected female
            values:
            - affected
            - F
            color: '#ff2121'
          - id: unaffected_male
            name: unaffected male
            values:
            - unaffected
            - M
            color: '#ffffff'
          - id: unaffected_female
            name: unaffected female
            values:
            - unaffected
            - F
            color: '#ffffff'
          default:
            id: unknown
            name: unknown
            color: '#aaaaaa'
        """)
    config = parse_person_set_collection_config(yaml.safe_load(content))
    return PersonSetCollection.from_families(config, families_fixture)
