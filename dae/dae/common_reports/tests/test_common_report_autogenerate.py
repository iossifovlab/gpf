# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os

import pytest

from dae.testing import setup_pedigree, setup_denovo, denovo_study
from dae.testing.foobar_import import foobar_gpf


@pytest.fixture
def trios2_fixture(tmp_path_factory):
    root_path = tmp_path_factory.mktemp(
        "common_reports_trios2")
    gpf_instance = foobar_gpf(root_path)
    ped_path = setup_pedigree(
        root_path / "trios2_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        f1       s1       d1     m1     2   1      sib
        f2       m2       0      0      2   1      mom
        f2       d2       0      0      1   1      dad
        f2       p2       d2     m2     1   2      prb
        """)
    denovo_path = setup_denovo(
        root_path / "trios2_data" / "in.tsv",
        """
          familyId  location  variant    bestState
          f1        foo:7     sub(A->G)  2||2||1||1/0||0||1||0
          f1        foo:10    sub(A->G)  2||2||1||1/0||0||1||1
          f2        foo:10    sub(A->G)  2||2||1/0||0||1
          f1        foo:11    sub(T->A)  2||2||1||2/0||0||1||0
          f1        bar:10    sub(G->A)  2||2||2||1/0||0||0||1
          f2        bar:11    sub(G->A)  2||2||1/0||0||1
          f2        bar:12    sub(G->A)  2||2||1/0||0||1
          f2        bar:14    del(2)     2||2||1/0||0||1
        """
    )

    study = denovo_study(
        root_path,
        "trios2", ped_path, [denovo_path],
        gpf_instance)
    return gpf_instance, study


def test_trios2_study_common_reports_enabled(trios2_fixture):
    _gpf_instance, study = trios2_fixture
    config = study.config

    assert config is not None
    assert config.common_report is not None

    assert config.common_report.enabled


def test_missing_common_report(trios2_fixture):
    gpf_instance, study = trios2_fixture
    report_filename = study.config.common_report.file_path
    assert os.path.exists(report_filename)
    os.remove(report_filename)

    assert not os.path.exists(report_filename)

    report = gpf_instance.get_common_report(study.study_id)
    assert report is not None

    assert os.path.exists(report_filename)
