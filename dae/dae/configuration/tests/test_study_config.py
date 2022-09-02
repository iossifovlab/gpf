# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pytest
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.study_config import study_config_schema


def test_study_with_study_filters_fails():
    study_config = {
        "id": "test",
        "genotype_browser": {
            "enabled": True,
            "has_study_filters": True
        },
    }
    with pytest.raises(ValueError) as err:
        GPFConfigParser.validate_config(
            study_config, study_config_schema, conf_dir=os.path.abspath(".")
        )
    print(err)


def test_dataset_with_study_filters_passes():
    study_config = {
        "id": "test",
        "studies": ["asdf"],
        "genotype_browser": {
            "enabled": True,
            "has_study_filters": True
        },
    }
    GPFConfigParser.validate_config(
        study_config, study_config_schema, conf_dir=os.path.abspath(".")
    )


def test_study_with_study_filters_false_passes():
    study_config = {
        "id": "test",
        "genotype_browser": {
            "enabled": True,
            "has_study_filters": False
        },
    }
    GPFConfigParser.validate_config(
        study_config, study_config_schema, conf_dir=os.path.abspath(".")
    )
