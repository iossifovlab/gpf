import pytest

from rest_framework import status

pytestmark = pytest.mark.usefixtures('mock_studies_manager')


def test_get_genomic_scores(user_client):
    url = '/api/v3/genomic_scores'
    response = user_client.get(url)
    assert status.HTTP_200_OK == response.status_code, repr(response.content)

    data = response.data
    assert data

    assert len(data) == 3

    assert sorted([gs['score'] for gs in data]) == \
        sorted(['SCORE-raw_rankscore', 'SCORE-raw', 'SCORE_phred'])
