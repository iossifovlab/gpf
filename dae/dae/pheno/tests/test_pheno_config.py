# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
from box import Box


def test_pheno_config_loading(fake_pheno_config: list[Box]) -> None:
    assert all(
        db.phenotype_data.name == "fake"
        for db in fake_pheno_config
    )
