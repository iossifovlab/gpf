"""Tests genotype study without genotype data."""
# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.common_reports.common_report import CommonReport
from dae.import_tools.cli import run_with_project
from dae.studies.study import GenotypeData
from dae.testing import StudyInputLayout, setup_import_project, setup_pedigree
from dae.testing.acgt_import import acgt_gpf


@pytest.fixture(scope="module")
def no_variants_study(
        tmp_path_factory: pytest.TempPathFactory) -> GenotypeData:
    root_path = tmp_path_factory.mktemp(
        "person_set_collection_test_study")
    gpf_instance = acgt_gpf(root_path)
    ped_path = setup_pedigree(
        root_path / "pedigree" / "in.ped",
        """
familyId personId dadId momId sex status role
f1       mom1     0     0     2   1      mom
f1       dad1     0     0     1   1      dad
f1       ch1      dad1  mom1  2   2      prb
f3       mom3     0     0     2   1      mom
f3       dad3     0     0     1   1      dad
f3       ch3      dad3  mom3  2   2      prb
        """)
    layout = StudyInputLayout("no_variants_study", ped_path, [], [], [], [])
    project = setup_import_project(root_path, layout, gpf_instance)
    run_with_project(project)

    gpf_instance.reload()
    return gpf_instance.get_genotype_data(layout.study_id)


def test_study_simple(no_variants_study: GenotypeData) -> None:
    """Test variants query for study without variants."""
    assert no_variants_study
    assert no_variants_study.study_id == "no_variants_study"

    fvs = list(no_variants_study.query_variants())
    assert len(fvs) == 0


def test_common_reports(no_variants_study: GenotypeData) -> None:
    """Test building a common report from a study without variants."""
    common_report = CommonReport.build_report(no_variants_study)
    assert common_report
