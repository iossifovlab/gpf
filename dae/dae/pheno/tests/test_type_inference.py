# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

import pytest
import yaml
from pydantic import ValidationError

from dae.pheno.common import InferenceConfig
from dae.pheno.pheno_import import merge_inference_configs


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
