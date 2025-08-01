# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from federation.remote_phenotype_data import RemotePhenotypeData
from federation.rest_api_client import RESTClient


@pytest.fixture
def t4c8_pheno(rest_client: RESTClient) -> RemotePhenotypeData:
    return RemotePhenotypeData({"id": "study_1_pheno"}, rest_client)


def test_get_measures_info(
    t4c8_pheno: RemotePhenotypeData, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GPF_PREFIX", "test_prefix")
    measures_info = t4c8_pheno.get_measures_info()

    assert measures_info["base_image_url"].startswith("/test_prefix")
