# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
from pathlib import Path

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.phenotype_data import regression_conf_schema
from dae.pheno.pheno_data import PhenotypeData, PhenotypeStudy
from dae.pheno.prepare_data import PreparePhenoBrowserBase
from dae.pheno.storage import PhenotypeStorageRegistry


def test_pheno_regressions_from_conf_path(regressions_conf: str) -> None:
    regs = GPFConfigParser.load_config(
        regressions_conf, regression_conf_schema,
    )
    expected_regs = {
        "reg1": {
            "instrument_name": "i1",
            "measure_name": "regressor1",
            "jitter": 0.1,
        },
        "reg2": {
            "instrument_name": "i1",
            "measure_name": "regressor2",
            "jitter": 0.2,
        },
        "reg3": {
            "instrument_name": "",
            "measure_name": "common_regressor",
            "jitter": 0.3,
        },
        "reg4": {
            "instrument_name": "i2",
            "measure_name": "regressor1",
            "jitter": 0.4,
        },
        "reg5": {
            "instrument_name": "",
            "measure_names": ["regressor2", "common_regressor"],
            "jitter": 0.1,
        },
    }

    assert len(regs.regression) == len(expected_regs)
    for reg_name, expected_reg in expected_regs.items():
        assert regs.regression[reg_name] == expected_reg


def test_has_regression_measure(
    fake_pheno_db_dir: Path,
    fake_pheno_storage_registry: PhenotypeStorageRegistry,
    fake_phenotype_data: PhenotypeStudy,
    tmp_path: Path,
    regressions_conf: str,
) -> None:
    fake_phenotype_data.cache_path = tmp_path
    reg = GPFConfigParser.load_config(regressions_conf, regression_conf_schema)
    browser = PhenotypeData.create_browser(
        fake_phenotype_data, read_only=False,
    )
    prep = PreparePhenoBrowserBase(
        fake_pheno_db_dir, fake_pheno_storage_registry, fake_phenotype_data,
        browser,
        cache_dir=tmp_path,
        images_dir=tmp_path / "images",
        pheno_regressions=reg["regression"],
    )

    expected_reg_measures = [
        ("regressor1", "i1"),
        ("regressor2", "i1"),
        ("common_regressor", ""),
        ("common_regressor", "i1"),
        ("common_regressor", "i2"),
        ("regressor1", "i2"),
        ("common_regressor", "i3"),
    ]

    for expected in expected_reg_measures:
        assert prep._has_regression_measure(*expected)
