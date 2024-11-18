# pylint: disable=W0621,C0114,C0116,W0212,W0613
from django.test.client import Client
from gpf_instance.gpf_instance import WGPFInstance


def test_gene_scores_list_view(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_scores"
    response = user_client.get(url)
    assert response.status_code == 200

    data = response.json()
    print([d["score"] for d in data])
    assert len(data) == 1

    for score in data:
        assert "desc" in score
        assert "score" in score
        assert "bars" in score
        assert "bins" in score


def test_gene_score_download(
    user_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    url = "/api/v3/gene_scores/download/t4c8_score"

    response = user_client.get(url)
    assert response.status_code == 200
    content = list(response.streaming_content)  # type: ignore
    assert len(content) > 0
    assert len(content[0].decode().split("\t")) == 2

    # This is due to a bug that downloaded empty list
    # the second time that request has been made

    response = user_client.get(url)
    assert response.status_code == 200
    assert len(list(response.streaming_content)) > 0  # type: ignore
