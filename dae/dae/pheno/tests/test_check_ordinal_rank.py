# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
from dae.pheno.common import MeasureType, default_config
from dae.pheno.pheno_data import PhenotypeStudy
from dae.pheno.prepare.measure_classifier import MeasureClassifier


def test_fake_phenotype_data_ordinal_m4(
    fake_phenotype_data: PhenotypeStudy,
) -> None:
    measure_id = "i1.m4"
    df = fake_phenotype_data.get_people_measure_values_df([measure_id])
    rank = len(df[measure_id].unique())
    assert rank == 9
    assert len(df) == 195

    measure_conf = default_config()
    classifier = MeasureClassifier(measure_conf)
    report = classifier.meta_measures(df[measure_id])
    assert classifier.classify(report) == MeasureType.ordinal
