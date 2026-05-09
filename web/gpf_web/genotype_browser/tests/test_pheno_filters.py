# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json

import pytest
from django.test import Client
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")

QUERY_URL = "/api/v3/genotype_browser/query"

FILTER_QUERY_CATEGORICAL = {
    "id": "Categorical",
    "from": "phenodb",
    "source": "instrument1.categorical",
    "sourceType": "categorical",
    "role": "prb",
    "selection": {"selection": ["option2"]},
}

FILTER_QUERY_CONTINUOUS = {
    "id": "Continuous",
    "from": "phenodb",
    "source": "instrument1.continuous",
    "sourceType": "continuous",
    "role": "prb",
    "selection": {"min": 3, "max": 4},
}

SOURCE_CONTINUOUS = {
    "source": "instrument1.continuous", "role": "prb", "format": "%s",
}

SOURCE_CATEGORICAL = {
    "source": "instrument1.categorical", "role": "prb", "format": "%s",
}

SOURCE_ORDINAL = {
    "source": "instrument1.ordinal", "role": "prb", "format": "%s",
}

SOURCE_RAW = {
    "source": "instrument1.raw", "role": "prb", "format": "%s",
}


@pytest.mark.xfail(reason="support for changing phenotype sources is broken")
@pytest.mark.parametrize(
    "pheno_filters,variants_count,preview_sources,pheno_values",
    [
        (
            [FILTER_QUERY_CATEGORICAL],
            3,
            [SOURCE_CATEGORICAL],
            [
                [["option2"]],
                [["option2"]],
                [["option2"]],
            ],
        ),
        (
            [FILTER_QUERY_CONTINUOUS],
            3,
            [SOURCE_CONTINUOUS],
            [
                [["3.14"]],
                [["3.14"]],
                [["3.14"]],
            ],
        ),
        (
            [FILTER_QUERY_CATEGORICAL, FILTER_QUERY_CONTINUOUS],
            3,
            [SOURCE_CATEGORICAL, SOURCE_CONTINUOUS],
            [
                [["option2"], ["3.14"]],
                [["option2"], ["3.14"]],
                [["option2"], ["3.14"]],
            ],
        ),
    ],
)
def test_query_with_pheno_filters(
    admin_client: Client,
    pheno_filters: list[dict],
    variants_count: int,
    pheno_values: list[list[str]],
    preview_sources: list[dict],
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    data = {
        "datasetId": "t4c8_study_1",
        "familyFilters": pheno_filters,
        "sources": preview_sources,
    }

    response = admin_client.post(
        QUERY_URL, json.dumps(data), content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    variants = list(response.streaming_content)  # type: ignore
    variants = json.loads("".join(x.decode("utf-8") for x in variants))
    assert len(variants) == variants_count
    assert variants == pheno_values
