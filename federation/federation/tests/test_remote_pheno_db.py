# pylint: disable=W0621,C0114,C0116,W0212,W0613
from federation.remote_phenotype_data import RemotePhenotypeData


def test_extract_url() -> None:
    extracted = RemotePhenotypeData._extract_pheno_dir(
        "testing/static/images/pheno_id",
    )
    assert extracted == "pheno_id"

    extracted = RemotePhenotypeData._extract_pheno_dir(
        "testing/static/images/pheno_id///",
    )
    assert extracted == "pheno_id"
