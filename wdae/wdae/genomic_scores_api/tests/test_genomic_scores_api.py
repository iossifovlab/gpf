# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines

import pytest
from rest_framework import status

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


def test_get_genomic_scores(user_client, wdae_gpf_instance):
    url = "/api/v3/genomic_scores"
    response = user_client.get(url)
    assert response.status_code == status.HTTP_200_OK, repr(response.content)

    data = response.data
    assert sorted([gs["score"] for gs in data]) == [
        "score0", "score0_incomplete_cov", "score2", "score4"]
