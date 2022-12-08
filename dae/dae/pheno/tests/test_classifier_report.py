# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
from dae.pheno.prepare.measure_classifier import MeasureClassifier


def test_fi1(fi1_df):
    for col in fi1_df:
        report = MeasureClassifier.meta_measures(fi1_df[col])
        assert (
            report.count_with_values
            == report.count_with_numeric_values
            + report.count_with_non_numeric_values
        )
        assert (
            report.count_total
            == report.count_with_values + report.count_without_values
        )
