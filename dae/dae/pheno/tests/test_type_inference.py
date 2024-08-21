# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

import pytest
import yaml
from pydantic import ValidationError

from dae.pheno.common import InferenceConfig
from dae.pheno.prepare.pheno_prepare import PrepareVariables


def test_valid_config_loads() -> None:

    config = yaml.safe_load(textwrap.dedent(
        """
        categorical:
          max_rank: 14
          min_rank: 1
        continuous:
          max_rank: null
          min_rank: 10
        measure_type: null
        min_individuals: 1
        non_numeric_cutoff: 0.06
        ordinal:
          max_rank: null
          min_rank: 1
        skip: false
        value_max_len: 32
        measure_type: ordinal
        """,
    ))

    assert InferenceConfig.parse_obj(config) is not None


def test_config_with_unknown_keys_errors() -> None:
    config = yaml.safe_load(textwrap.dedent(
        """
        categorical:
          max_rank: 14
          min_rank: 1
        continuous:
          max_rank: null
          min_rank: 10
        measure_type: null
        min_individuals: 1
        non_numeric_cutoff: 0.06
        ordinal:
          max_rank: null
          min_rank: 1
        skip: false
        value_max_len: 32
        measure_type: ordinal
        some_key: asdf
        another_key: dkfhjldfjh
        """,
    ))
    with pytest.raises(ValidationError):
        InferenceConfig.parse_obj(config)


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
          measure_type: null
          min_individuals: 1
          non_numeric_cutoff: 0.06
          skip: false
          value_max_len: 32

        "some_instrument.*":
          categorical:
            max_rank: 16
            min_rank: 2

        "*.some_measure":
          measure_type: ordinal

        "another_instrument.some_measure":
          skip: true
        """,
    ))

    config = PrepareVariables.merge_inference_configs(
        configs,
        "some_instrument",
        "another_measure",
    )

    assert config.categorical.max_rank == 16
    assert config.categorical.min_rank == 2
    assert config.measure_type is None
    assert config.skip is False

    config = PrepareVariables.merge_inference_configs(
        configs,
        "some_instrument",
        "some_measure",
    )

    assert config.categorical.max_rank == 16
    assert config.categorical.min_rank == 2
    assert config.measure_type == "ordinal"
    assert config.skip is False

    config = PrepareVariables.merge_inference_configs(
        configs,
        "asdf",
        "ghjk",
    )

    assert config.categorical.max_rank == 14
    assert config.categorical.min_rank == 1
    assert config.measure_type is None
    assert config.skip is False

    config = PrepareVariables.merge_inference_configs(
        configs,
        "another_instrument",
        "some_measure",
    )

    assert config.categorical.max_rank == 14
    assert config.categorical.min_rank == 1
    assert config.measure_type == "ordinal"
    assert config.skip is True
