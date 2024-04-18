# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json

from django.test import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status


def test_study_with_phenotype_data(wdae_gpf_instance: WGPFInstance) -> None:
    wrapper = wdae_gpf_instance.get_wdae_wrapper("comp")

    assert wrapper is not None
    assert wrapper.phenotype_data is not None


def test_pheno_measure_genotype_browser_columns(
    admin_client: Client,
    wdae_gpf_instance: WGPFInstance,
) -> None:
    data = {
        "datasetId": "comp",
        "familyIds": ["f5"],
    }
    response = admin_client.post(
        "/api/v3/genotype_browser/query",
        json.dumps(data), content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    lines = json.loads(
        "".join(
            map(lambda x: x.decode("utf-8"),
                response.streaming_content)))  # type: ignore
    assert len(lines) == 6

    assert len(lines[1]) == 10
    line = lines[1]

    assert line[0] == ["f5"]
    assert line[8] == ["171.890"]
    assert line[9] == ["38.886"]

# f5.p1   171.890375  i1.age.prb
# f5.p1   38.885845   i1.iq.prb
