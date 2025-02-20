# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import textwrap

import pytest
import yaml

from dae.genomic_resources.testing import setup_directories, setup_pedigree
from dae.pheno.common import DestinationConfig, PhenoImportConfig
from dae.pheno.pheno_data import PhenotypeStudy
from dae.pheno.pheno_import import import_pheno_data


@pytest.fixture(scope="module")
def pheno_study(
    tmp_path_factory: pytest.TempPathFactory,
) -> PhenotypeStudy:
    root_path = tmp_path_factory.mktemp("pheno_import")
    ped_path = setup_pedigree(
        root_path / "pedigree.ped",
        """
        familyId	personId	dadId	momId	sex	status	role	layout	test_col
        fam1	fam1.mom	0	0	2	1	mom	1:53.5,50.0	test1
        fam1	fam1.dad	0	0	1	1	dad	1:10.0,50.0	test2
        fam1	fam1.prb	fam1.dad	fam1.mom	2	2	prb	2:31.75,80.0	test3
        fam2	fam2.mom	0	0	2	1	mom	1:53.5,50.0	test4
        fam2	fam2.dad	0	0	1	1	dad	1:10.0,50.0	test5
        fam2	fam2.prb	fam2.dad	fam2.mom	2	2	prb	2:31.75,80.0	test6
        fam3	fam3.mom	0	0	2	1	mom	1:53.5,50.0	test7
        fam3	fam3.dad	0	0	1	1	dad	1:10.0,50.0	test8
        fam3	fam3.prb	fam3.dad	fam3.mom	2	2	prb	2:31.75,80.0	test9
        fam4	fam4.mom	0	0	2	1	mom	1:53.5,50.0	test10
        fam4	fam4.dad	0	0	1	1	dad	1:10.0,50.0	test11
        fam4	fam4.prb	fam4.dad	fam4.mom	2	2	prb	2:31.75,80.0	test12
        """)  # noqa: E501
    setup_directories(root_path, {
        "instruments": {
            "instr1.csv": textwrap.dedent("""
                person_id,m1,m2,m3
                fam1.mom,1,8,3
                fam1.dad,3,1,3
                fam1.prb,4,0,3
                fam2.mom,9,4,3
                fam2.dad,10,,3
                fam2.prb,23,asdf,3
            """),
        },
    })

    instruments_dir = root_path / "instruments"
    out_dir = root_path / "out"
    storage_dir = tmp_path_factory.mktemp("test_storage_dir")

    import_config = PhenoImportConfig(
        id="test",
        input_dir=str(root_path),
        work_dir=str(out_dir),
        instrument_files=[str(instruments_dir)],
        pedigree=str(ped_path),
        person_column="person_id",
        destination=DestinationConfig(storage_dir=str(storage_dir)),
    )

    pheno_config = yaml.safe_load(textwrap.dedent(f"""
        common_report:
          enabled: True
          file_path: "{out_dir}/common_report.json"
          draw_all_families: False
          selected_person_set_collections:
            family_report:
              - "phenotype"

        person_set_collections:
          selected_person_set_collections:
            - "phenotype"
          phenotype:
            id: "phenotype"
            name: "Phenotype"
            sources:
              - from: "pedigree"
                source: "status"
            domain:
              - id: "autism"
                name: "autism"
                values:
                  - "affected"
                color: "#ff2121"
              - id: "unaffected"
                name: "unaffected"
                values:
                  - "unaffected"
                color: "#ffffff"
            default:
              id: "unspecified"
              name: "unspecified"
              color: "#aaaaaa"
        """))

    import_pheno_data(import_config)

    return PhenotypeStudy(
        "test",
        str(storage_dir / "test" / "test.db"),
        pheno_config,
    )


def test_study_families(pheno_study: PhenotypeStudy):
    families = pheno_study.families
    assert families is not None
    assert len(families) == 4
    assert len(families.persons) == 12


def test_study_person_sets(pheno_study: PhenotypeStudy):
    person_set_collections = pheno_study.person_set_collections

    assert len(person_set_collections) == 1
    assert "phenotype" in person_set_collections

    assert len(person_set_collections["phenotype"].person_sets) == 2
    assert "autism" in person_set_collections["phenotype"].person_sets
    assert "unaffected" in person_set_collections["phenotype"].person_sets

    assert len(person_set_collections["phenotype"].person_sets["autism"]) == 4
    assert len(person_set_collections["phenotype"].person_sets["unaffected"]) == 8  # noqa: E501


def test_study_common_report(pheno_study: PhenotypeStudy):
    common_report = pheno_study.get_common_report()
    assert common_report is not None
    assert common_report.people_report is not None
    assert common_report.families_report is not None
    assert common_report.families_report.families_counters is not None
