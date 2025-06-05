# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

import pytest
import yaml
from pydantic import ValidationError

from dae.genomic_resources.histogram import (
    NumberHistogram,
    NumberHistogramConfig,
)
from dae.pheno.common import (
    InferenceConfig,
    MeasureHistogramConfigs,
    MeasureType,
)
from dae.pheno.pheno_import import (
    MeasureReport,
    merge_histogram_configs,
    merge_inference_configs,
)
from dae.pheno.prepare.measure_classifier import InferenceReport


def test_valid_config_loads() -> None:

    config = yaml.safe_load(textwrap.dedent(
        """
        categorical:
          max_rank: 14
          min_rank: 1
        continuous:
          max_rank: null
          min_rank: 10
        min_individuals: 1
        non_numeric_cutoff: 0.06
        ordinal:
          max_rank: null
          min_rank: 1
        skip: false
        value_max_len: 32
        histogram_type: categorical
        """,
    ))

    assert InferenceConfig.model_validate(config) is not None


def test_config_with_unknown_keys_errors() -> None:
    config = yaml.safe_load(textwrap.dedent(
        """
        categorical:
          max_rank: 14
          min_rank: 1
        continuous:
          max_rank: null
          min_rank: 10
        min_individuals: 1
        non_numeric_cutoff: 0.06
        ordinal:
          max_rank: null
          min_rank: 1
        skip: false
        value_max_len: 32
        histogram_type: categorical
        some_key: asdf
        another_key: dkfhjldfjh
        """,
    ))
    with pytest.raises(ValidationError):
        InferenceConfig.model_validate(config)


def test_merge() -> None:
    configs = yaml.safe_load(textwrap.dedent(
        """
        "*.*":
          categorical:
            max_rank: 14
            min_rank: 1
          continuous:
            max_rank: null
            min_rank: 10
          min_individuals: 1
          non_numeric_cutoff: 0.06
          skip: false
          value_max_len: 32

        "some_instrument.*":
          categorical:
            max_rank: 16
            min_rank: 2

        "*.some_measure":
          histogram_type: categorical

        "another_instrument.some_measure":
          skip: true
        """,
    ))

    config = merge_inference_configs(
        configs,
        "some_instrument",
        "another_measure",
    )

    assert config.categorical.max_rank == 16
    assert config.categorical.min_rank == 2
    assert config.histogram_type is None
    assert config.skip is False

    config = merge_inference_configs(
        configs,
        "some_instrument",
        "some_measure",
    )

    assert config.categorical.max_rank == 16
    assert config.categorical.min_rank == 2
    assert config.histogram_type == "categorical"
    assert config.skip is False

    config = merge_inference_configs(
        configs,
        "asdf",
        "ghjk",
    )

    assert config.categorical.max_rank == 14
    assert config.categorical.min_rank == 1
    assert config.histogram_type is None
    assert config.skip is False

    config = merge_inference_configs(
        configs,
        "another_instrument",
        "some_measure",
    )

    assert config.categorical.max_rank == 14
    assert config.categorical.min_rank == 1
    assert config.histogram_type == "categorical"
    assert config.skip is True


def test_merge_config_histograms() -> None:

    inference_report = InferenceReport.model_validate({
        "value_type": str,
        "histogram_type": NumberHistogram,
        "min_individuals": 0,
        "count_total": 0,
        "count_with_values": 0,
        "count_without_values": 0,
        "count_unique_values": 0,
        "min_value": 0,
        "max_value": 0,
        "values_domain": "",
    })

    configs = MeasureHistogramConfigs.model_validate(
        yaml.safe_load(textwrap.dedent(
          """
          number_config:
            "some_instrument.*":
              number_of_bins: 5
            "*.some_measure":
              number_of_bins: 10
            "another_instrument.some_measure":
              number_of_bins: 15
          """,
      )),
    )

    config = merge_histogram_configs(
        configs,
        MeasureReport.model_validate({
            "measure_name": "some_other_measure",
            "instrument_name": "some_instrument",
            "instrument_description": "instrument description",
            "inference_report": inference_report,
            "db_name": "",
            "measure_type": MeasureType.continuous,
        }),
    )

    assert isinstance(config, NumberHistogramConfig)
    assert config.number_of_bins == 5

    config = merge_histogram_configs(
        configs,
        MeasureReport.model_validate({
            "measure_name": "some_measure",
            "instrument_name": "some_instrument",
            "instrument_description": "instrument description",
            "inference_report": inference_report,
            "db_name": "",
            "measure_type": MeasureType.continuous,
        }),
    )

    assert isinstance(config, NumberHistogramConfig)
    assert config.number_of_bins == 10

    config = merge_histogram_configs(
        configs,
        MeasureReport.model_validate({
            "measure_name": "some_measure",
            "instrument_name": "another_instrument",
            "instrument_description": "instrument description",
            "inference_report": inference_report,
            "db_name": "",
            "measure_type": MeasureType.continuous,
        }),
    )

    assert isinstance(config, NumberHistogramConfig)
    assert config.number_of_bins == 15
