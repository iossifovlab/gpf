# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from dae.studies.study import GenotypeData
from dae.testing import denovo_study, setup_denovo, setup_pedigree
from dae.testing.foobar_import import foobar_gpf


@pytest.fixture
def trios2_study(tmp_path_factory: pytest.TempPathFactory) -> GenotypeData:
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
          chrom  pos  ref  alt  person_id
          foo    7    A    G    p1
          foo    10   A    G    p1
          foo    10   A    G    p2
          foo    11   T    A    p1
          bar    10   G    A    s1
          bar    11   G    A    p2
          bar    12   G    A    p2
          bar    14   G    A    p2
        """,
    )

    return denovo_study(
        root_path,
        "trios2", ped_path, [denovo_path],
        gpf_instance)


def test_trios2_study_common_reports_enabled(
    trios2_study: GenotypeData,
) -> None:
    config = trios2_study.config

    assert config is not None
    assert config.common_report is not None

    assert config.common_report.enabled


def test_trios2_study_denovo_report_effect_groups(
    trios2_study: GenotypeData,
) -> None:
    common_report = trios2_study.config.common_report
    assert common_report.enabled
    assert common_report.effect_groups == [
        "LGDs", "nonsynonymous", "UTRs",
    ]


def test_trios2_study_denovo_report_effect_types(
    trios2_study: GenotypeData,
) -> None:
    common_report = trios2_study.config.common_report
    assert common_report.enabled
    assert common_report.effect_types == [
        "Nonsense", "Frame-shift", "Splice-site", "Missense",
        "No-frame-shift", "noStart", "noEnd", "Synonymous",
        "Non coding", "Intron", "Intergenic", "3'-UTR", "5'-UTR",
    ]
