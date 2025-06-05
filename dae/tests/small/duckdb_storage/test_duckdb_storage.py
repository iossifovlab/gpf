# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.studies.study import GenotypeData


def test_imported_study(imported_study: GenotypeData) -> None:
    assert imported_study is not None


def test_imported_study_family_variants(imported_study: GenotypeData) -> None:
    vs = list(imported_study.query_variants())

    assert len(vs) == 2


def test_imported_study_summary_variants(imported_study: GenotypeData) -> None:
    vs = list(imported_study.query_summary_variants())

    assert len(vs) == 2
