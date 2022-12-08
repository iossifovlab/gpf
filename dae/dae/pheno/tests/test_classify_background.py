# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
from dae.pheno.prepare.measure_classifier import MeasureClassifier
from dae.pheno.common import default_config, MeasureType
from dae.pheno.prepare.pheno_prepare import PrepareVariables


def test_fake_background_classify(fake_background_df):

    columns = list(fake_background_df.columns)
    for col in columns[1:]:
        series = fake_background_df[col]

        classifier = MeasureClassifier(default_config())
        classifier_report = MeasureClassifier.meta_measures(series)
        measure_type = classifier.classify(classifier_report)

        assert (
            measure_type == MeasureType.text
            or measure_type == MeasureType.raw
            or measure_type == MeasureType.categorical
        )

        values = [
            v for v in classifier.convert_to_string(series.values)
            if v is not None
        ]
        assert all(isinstance(v, str) for v in values)


def test_fake_background_build(
    test_config, fake_ped_file, fake_background_filename
):
    test_config.person.role.mapping = "INTERNAL"

    prep = PrepareVariables(test_config)
    assert prep is not None

    prep.build_pedigree(fake_ped_file)
    instrument_df = prep.load_instrument(
        "background", [fake_background_filename]
    )

    df = prep.build_instrument("background", instrument_df)
    assert df is not None
    assert len(df) == 195
