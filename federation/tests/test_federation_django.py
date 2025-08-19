# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
from typing import cast

import pytest
from django.http import StreamingHttpResponse
from django.test.client import Client
from federation.remote_study_wrapper import RemoteWDAEStudy
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework import status
from studies.query_transformer import QueryTransformer
from studies.response_transformer import ResponseTransformer


def test_studies(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    expected_ids = {
        "t4c8_dataset", "t4c8_study_1", "TEST_REMOTE_t4c8_dataset",
        "TEST_REMOTE_t4c8_study_1", "t4c8_study_2", "TEST_REMOTE_t4c8_study_4",
        "study_1_pheno", "TEST_REMOTE_t4c8_study_2",
        "TEST_REMOTE_study_1_pheno", "t4c8_study_4",
    }

    response = admin_client.get("/api/v3/datasets")
    assert response is not None
    assert response.status_code == 200

    dataset_ids = {item["id"] for item in response.json()["data"]}
    assert dataset_ids == expected_ids


def test_genomic_scores(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    expected_scores = {"score_one", "TEST_REMOTE_score_one"}

    response = admin_client.get("/api/v3/genomic_scores")
    assert response
    assert response.status_code == 200

    returned_scores = {item["score"] for item in response.json()}
    assert returned_scores == expected_scores


def test_gene_sets(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    expected_names = {"main", "denovo", "TEST_REMOTE_main"}

    response = admin_client.get("/api/v3/gene_sets/gene_sets_collections")
    assert response
    assert response.status_code == 200

    returned_names = {item["name"] for item in response.json()}
    assert returned_names == expected_names


def test_measures_regressions(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    expected_measures = {"age", "iq"}

    response = admin_client.get(
        "/api/v3/measures/regressions?datasetId=TEST_REMOTE_study_1_pheno")
    assert response
    assert response.status_code == 200

    returned_measures = set(response.json().keys())
    assert returned_measures == expected_measures


def test_pheno_tool(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    query = {
        "datasetId": "TEST_REMOTE_t4c8_study_1",
        "measureId": "i1.m1",
        "normalizeBy": [],
        "effectTypes": ["missense", "frame-shift", "synonymous"],
        "presentInParent": {"presentInParent": ["neither"]},
    }

    response = admin_client.post(
        "/api/v3/pheno_tool",
        data=json.dumps(query),
        content_type="application/json",
    )
    assert response.status_code == 200

    results = response.json()["results"]
    assert len(results) == 3

    results_by_effect = {r["effect"]: r for r in results}

    missense = results_by_effect["missense"]
    assert missense["femaleResults"]["positive"]["count"] == 1
    assert missense["femaleResults"]["positive"]["mean"] == \
        pytest.approx(110.71112823486328, abs=1e-3)
    assert missense["femaleResults"]["negative"]["count"] == 1
    assert missense["femaleResults"]["negative"]["mean"] == \
        pytest.approx(96.634521484375, abs=1e-3)
    assert missense["maleResults"]["positive"]["count"] == 0
    assert missense["maleResults"]["negative"]["count"] == 0

    frameshift = results_by_effect["frame-shift"]
    assert frameshift["femaleResults"]["negative"]["count"] == 2
    assert frameshift["femaleResults"]["negative"]["mean"] == \
        pytest.approx(103.67282485961914, abs=1e-3)
    assert frameshift["femaleResults"]["positive"]["count"] == 0
    assert frameshift["femaleResults"]["positive"]["mean"] == \
        pytest.approx(103.67282485961914, abs=1e-3)
    assert frameshift["maleResults"]["positive"]["count"] == 0
    assert frameshift["maleResults"]["negative"]["count"] == 0

    synonymous = results_by_effect["synonymous"]
    assert synonymous["femaleResults"]["positive"]["count"] == 1
    assert synonymous["femaleResults"]["positive"]["mean"] == \
        pytest.approx(96.634521484375, abs=1e-3)
    assert synonymous["femaleResults"]["negative"]["count"] == 1
    assert synonymous["femaleResults"]["negative"]["mean"] == \
        pytest.approx(110.71112823486328, abs=1e-3)
    assert synonymous["maleResults"]["positive"]["count"] == 0
    assert synonymous["maleResults"]["negative"]["count"] == 0


def test_enrichment_models(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    response = admin_client.get(
        "/api/v3/enrichment/models/TEST_REMOTE_t4c8_dataset")
    assert response
    assert response.status_code == 200
    result = response.json()

    assert result["background"][0]["id"] == "coding_len_background"
    assert result["counting"][0]["id"] == "enrichment_gene_counting"
    assert result["counting"][1]["id"] == "enrichment_events_counting"
    assert result["defaultBackground"] == "coding_len_background"
    assert result["defaultCounting"] == "enrichment_gene_counting"


def test_enrichment_test(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    query = {
        "datasetId": "TEST_REMOTE_t4c8_dataset",
        "enrichmentBackgroundModel": "coding_len_background",
        "enrichmentCountingModel": "enrichment_gene_counting",
        "geneSet": {
            "geneSetsCollection": "main",
            "geneSet": "t4_candidates",
        },
    }
    response = admin_client.post(
        "/api/v3/enrichment/test",
        data=json.dumps(query),
        content_type="application/json",
    )

    assert response
    assert response.status_code == 200

    result_remote = response.data  # type: ignore
    assert set(result_remote.keys()) == {"desc", "result"}
    assert result_remote["desc"] == "Gene Set: T4 Candidates (1)"
    assert len(result_remote["result"]) == 4

    query["datasetId"] = "t4c8_dataset"
    response = admin_client.post(
        "/api/v3/enrichment/test",
        data=json.dumps(query),
        content_type="application/json",
    )
    result_local = response.data  # type: ignore
    assert result_local == result_remote


def test_gene_view_config(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    response = admin_client.get(
        "/api/v3/gene_view/config?datasetId=TEST_REMOTE_t4c8_study_1",
    )
    assert response.status_code == status.HTTP_200_OK


def test_gene_view_summary_variants_query(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    data = {"datasetId": "TEST_REMOTE_t4c8_study_1", "geneSymbols": ["t4"]}
    response = admin_client.post(
        "/api/v3/gene_view/query_summary_variants",
        json.dumps(data),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    res = response.data  # type: ignore
    assert len(res) == 1
    assert len(res[0]["alleles"]) == 1


def test_gene_view_summary_variants_download(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    data = {
        "queryData": json.dumps({
            "datasetId": "TEST_REMOTE_t4c8_study_1",
            "geneSymbols": ["t4"],
            "download": True,
        }),
    }

    response = admin_client.post(
        "/api/v3/gene_view/download_summary_variants",
        json.dumps(data),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    lines = list(response.streaming_content)  # type: ignore
    assert len(lines) == 3


def test_query_variants_wdae_remote(
    t4c8_wgpf_instance: WGPFInstance,
    t4c8_query_transformer: QueryTransformer,
    t4c8_response_transformer: ResponseTransformer,
) -> None:
    remote_study = t4c8_wgpf_instance.get_wdae_wrapper(
        "TEST_REMOTE_t4c8_study_1")
    assert remote_study is not None
    assert isinstance(remote_study, RemoteWDAEStudy)

    result = list(remote_study.query_variants_wdae(
        {}, [], t4c8_query_transformer, t4c8_response_transformer))
    assert len(result) == 12


def test_query_variants_wdae_remote_download(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    data = {
        "datasetId": "TEST_REMOTE_t4c8_study_1",
        "download": True,
    }
    response = admin_client.post(
        "/api/v3/genotype_browser/query",
        json.dumps(data),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    res = "".join([
        p.decode("utf8")
        for p in response.streaming_content
    ]).split("\n")
    res = [r for r in res if r]
    assert len(res) == 13


def test_genotype_browser_query_default_person_set_collection(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    data = {"datasetId": "TEST_REMOTE_t4c8_study_1"}
    response = admin_client.post(
        "/api/v3/genotype_browser/query",
        json.dumps(data),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK

    res = "".join(
        p.decode("utf8") for p in response.streaming_content if p).split("\n")
    res = [r for r in res if r]

    first_row = json.loads(res[0])
    assert any(
        cell[6] != "#ffffff"
        for row in first_row
        for cell in row[4]
    )


def test_genotype_browser_query_explicit_person_set_collection(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    data = {
        "datasetId": "TEST_REMOTE_t4c8_study_1",
        "personSetCollection": {
            "id": "phenotype",
            "checkedValues": ["autism"],
        },
    }

    response = admin_client.post(
        "/api/v3/genotype_browser/query",
        json.dumps(data),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK

    res = "".join(
        p.decode("utf8") for p in response.streaming_content if p).split("\n")
    res = [r for r in res if r]

    first_row = json.loads(res[0])
    assert any(
        cell[6] != "#ffffff"
        for row in first_row
        for cell in row[4]
    )


@pytest.mark.parametrize(
    "dataset_id", [
        "t4c8_study_1",
        "TEST_REMOTE_t4c8_study_1",

])
def test_pheno_browser_instruments(
    admin_client: Client,
    dataset_id: str,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    instruments_url = "/api/v3/pheno_browser/instruments"
    response = admin_client.get(
        instruments_url,
        {
            "dataset_id": dataset_id,
        },
    )

    assert response.status_code == 200

    assert len(response.json()["instruments"]) == 2
    assert set(response.json()["instruments"]) == {"i1", "pheno_common"}


def test_pheno_browser_measures_info(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    info_url = "/api/v3/pheno_browser/measures_info"
    response_remote = admin_client.get(
        info_url,
        {
            "dataset_id": "TEST_REMOTE_t4c8_study_1",
        },
    )

    assert response_remote.status_code == 200

    response_local = admin_client.get(
        info_url,
        {
            "dataset_id": "t4c8_study_1",
        },
    )

    assert response_local.status_code == 200

    remote_json = response_remote.json()
    local_json = response_remote.json()

    assert remote_json["has_descriptions"] == local_json["has_descriptions"]
    assert remote_json["regression_names"] == local_json["regression_names"]
    assert remote_json["base_image_url"] == (
        "api/v3/pheno_browser/images/TEST_REMOTE_"
    )


def test_pheno_browser_measure_description(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    descriptions_url = "/api/v3/pheno_browser/measure_description"
    response_remote = admin_client.get(
        descriptions_url,
        {
            "dataset_id": "TEST_REMOTE_t4c8_study_1",
            "measure_id": "i1.m1",
        },
    )

    assert response_remote.status_code == 200

    response_local = admin_client.get(
        descriptions_url,
        {
            "dataset_id": "t4c8_study_1",
            "measure_id": "i1.m1",
        },
    )

    assert response_local.status_code == 200

    assert response_remote.json() == response_local.json()


def test_pheno_browser_measures_search(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    measures_url = "/api/v3/pheno_browser/measures"
    response_remote = admin_client.get(
        measures_url,
        {
            "dataset_id": "TEST_REMOTE_t4c8_study_1",
            "instrument": "i1",
            "search": "m1",
        },
    )

    assert response_remote.status_code == 200

    response_local = admin_client.get(
        measures_url,
        {
            "dataset_id": "t4c8_study_1",
            "instrument": "i1",
            "search": "m1",
        },
    )

    assert response_local.status_code == 200

    assert response_remote.json() == response_local.json()


def test_pheno_browser_download(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    download_url = "/api/v3/pheno_browser/download"
    response_remote = cast(StreamingHttpResponse, admin_client.get(
        download_url,
        {
            "dataset_id": "TEST_REMOTE_t4c8_study_1",
            "instrument": "i1",
            "search_term": "m1",
        },
    ))

    assert response_remote.status_code == 200

    response_local = cast(StreamingHttpResponse, admin_client.get(
        download_url,
        {
            "dataset_id": "t4c8_study_1",
            "instrument": "i1",
            "search_term": "m1",
        },
    ))

    assert response_local.status_code == 200

    assert b"".join(map(bytes, response_remote)) == \
        b"".join(map(bytes, response_local))


def test_pheno_browser_download_check(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    download_url = "/api/v3/pheno_browser/download"
    response_remote = cast(StreamingHttpResponse, admin_client.head(
        download_url,
        {
            "dataset_id": "TEST_REMOTE_t4c8_study_1",
            "instrument": "i1",
            "search_term": "m1",
        },
    ))

    response_local = cast(StreamingHttpResponse, admin_client.head(
        download_url,
        {
            "dataset_id": "t4c8_study_1",
            "instrument": "i1",
            "search_term": "m1",
        },
    ))

    assert response_remote.status_code == response_local.status_code


def test_pheno_browser_measure_count(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    measures_count_url = "/api/v3/pheno_browser/measures_count"
    response_remote = admin_client.get(
        measures_count_url,
        {
            "dataset_id": "TEST_REMOTE_t4c8_study_1",
            "instrument": "i1",
            "search_term": "m",
        },
    )

    response_local = admin_client.get(
        measures_count_url,
        {
            "dataset_id": "t4c8_study_1",
            "instrument": "i1",
            "search_term": "m",
        },
    )

    assert response_remote.json() == response_local.json()


def test_pheno_browser_image_links(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    response_info = admin_client.get(
        "/api/v3/pheno_browser/measures_info",
        {
            "dataset_id": "TEST_REMOTE_study_1_pheno",
        },
    )
    response_measures = admin_client.get(
        "/api/v3/pheno_browser/measures",
        {
            "dataset_id": "TEST_REMOTE_study_1_pheno",
            "instrument": "i1",
            "search_term": "m",
        },
    )
    url = response_info.json()["base_image_url"]
    image_path = response_measures.json()[0]["measure"]["figure_distribution"]

    assert url + image_path == (
        "api/v3/pheno_browser/images/"
        "TEST_REMOTE_study_1_pheno/i1/i1.age.violinplot.png"
    )


def test_variant_reports(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    common_report_url = (
        "/api/v3/common_reports/studies/"
    )
    response_remote = admin_client.get(
        common_report_url + "TEST_REMOTE_t4c8_study_1")

    assert response_remote.json()["denovo_report"]["tables"][0]["rows"][0] == {
        "effect_type": "LGDs",
        "row": [
            {
                "column": "autism (2)",
                "number_of_children_with_event": 1,
                "number_of_observed_events": 1,
                "observed_rate_per_child": 0.5,
                "percent_of_children_with_events": 0.5,
            },
            {
                "column": "unaffected (2)",
                "number_of_children_with_event": 0,
                "number_of_observed_events": 0,
                "observed_rate_per_child": 0,
                "percent_of_children_with_events": 0,
            },
        ],
    }


def test_full_variant_reports(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    common_report_url = (
        "/api/v3/common_reports/studies/"
    )
    response_remote = admin_client.get(
        common_report_url + "TEST_REMOTE_t4c8_study_1" + "/full")

    res_data = response_remote.json()
    assert res_data == {}
    assert res_data[
        "families_report"][0]["counters"][0]["pedigree"][0] == [
            "f1.1", "mom1", "0", "0", "F", "mom",
            "#ffffff", "1:10.0,50.0", False, "", "",
        ]
    assert res_data[
        "families_report"][0]["counters"][0]["pedigree"][3] == [
            "f1.1", "s1", "mom1", "dad1", "M", "sib",
            "#ffffff", "2:10.0,80.0", False, "", "",
        ]


def test_family_counter_list(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    family_counter_url = (
        "/api/v3/common_reports/family_counters"
    )

    response_remote = admin_client.post(
        family_counter_url,
        {
            "study_id": "TEST_REMOTE_t4c8_study_1",
            "group_name": "Phenotype",
            "counter_id": 0,
        },
    )
    counter_one = response_remote.json()
    assert counter_one == ["f1.1"]

    response_remote = admin_client.post(
        family_counter_url,
        {
            "study_id": "TEST_REMOTE_t4c8_study_1",
            "group_name": "Phenotype",
            "counter_id": 1,
        },
    )
    counter_two = response_remote.json()
    assert counter_two == ["f1.3"]


def test_family_counter_download(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    url = "/api/v3/common_reports/family_counters/download"
    data = {
        "queryData": json.dumps({
            "study_id": "TEST_REMOTE_t4c8_study_1",
            "group_name": "Phenotype",
            "counter_id": "0",
        }),
    }
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json",
    )

    assert response
    assert response.status_code == status.HTTP_200_OK

    text = b"".join(list(response.streaming_content)).decode()  # type: ignore
    lines = text.split("\n")

    assert lines[0] == (
        "familyId\tpersonId\tmomId\tdadId\tsex\tstatus\trole\t"
        "sample_id\tlayout\tgenerated\tnot_sequenced\ttag_nuclear_family\t"
        "tag_quad_family\ttag_trio_family\ttag_simplex_family\t"
        "tag_multiplex_family\ttag_control_family\ttag_affected_dad_family\t"
        "tag_affected_mom_family\ttag_affected_prb_family\t"
        "tag_affected_sib_family\ttag_unaffected_dad_family\t"
        "tag_unaffected_mom_family\ttag_unaffected_prb_family\t"
        "tag_unaffected_sib_family\ttag_male_prb_family\t"
        "tag_female_prb_family\ttag_missing_mom_family\t"
        "tag_missing_dad_family\tmember_index\tphenotype"
    )
    assert lines[1] == (
        "f1.1\tmom1\t0\t0\tF\tunaffected\tmom\tmom1\t1:10.0,50.0"
        "\tFalse\tFalse\tTrue\tTrue\tFalse\tTrue\tFalse\tFalse\t"
        "False\tFalse\tTrue\tFalse\tTrue\tTrue\tFalse\tTrue\t"
        "False\tTrue\tFalse\tFalse\t0\tunaffected"
    )
    assert lines[2] == (
        "f1.1\tdad1\t0\t0\tM\tunaffected\tdad\tdad1\t1:39.0,50.0"
        "\tFalse\tFalse\tTrue\tTrue\tFalse\tTrue\tFalse\tFalse\t"
        "False\tFalse\tTrue\tFalse\tTrue\tTrue\tFalse\tTrue\tFalse"
        "\tTrue\tFalse\tFalse\t1\tunaffected"
    )


def test_families_data_download(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    url = (
        "/api/v3/common_reports/families_data/TEST_REMOTE_t4c8_dataset"
    )
    response = admin_client.get(url)

    assert response
    assert response.status_code == status.HTTP_200_OK

    text = b"".join(list(response.streaming_content)).decode()  # type: ignore
    lines = text.split("\n")
    assert len(lines) == 17
    assert lines[0] == (
        "familyId\tpersonId\tmomId\tdadId\tsex\tstatus\trole\tsample_id\t"
        "layout\tgenerated\tnot_sequenced\ttag_nuclear_family\t"
        "tag_quad_family\ttag_trio_family\ttag_simplex_family\t"
        "tag_multiplex_family\ttag_control_family\ttag_affected_dad_family\t"
        "tag_affected_mom_family\ttag_affected_prb_family\t"
        "tag_affected_sib_family\ttag_unaffected_dad_family\t"
        "tag_unaffected_mom_family\ttag_unaffected_prb_family\t"
        "tag_unaffected_sib_family\ttag_male_prb_family\t"
        "tag_female_prb_family\ttag_missing_mom_family\t"
        "tag_missing_dad_family\tmember_index\tphenotype"
    )
    assert (
        "f2.1\tch1\tmom1\tdad1\tF\taffected\tprb\tch1\t2:31.75,80.0\t"
        "False\tFalse\tTrue\tFalse\tTrue\tTrue\tFalse\tFalse\tFalse\t"
        "False\tTrue\tFalse\tTrue\tTrue\tFalse\tFalse\t"
        "False\tTrue\tFalse\tFalse\t2\tepilepsy"
    ) in lines


def test_families_tags_download(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    url = (
        "/api/v3/common_reports/families_data/TEST_REMOTE_t4c8_dataset"
    )
    body = {
        "queryData": json.dumps({
            "tagsQuery": {
                "orMode": False,
                "includeTags": ["tag_nuclear_family", "tag_trio_family"],
                "excludeTags": [],
            },
        }),
    }
    response = admin_client.post(
        url, data=json.dumps(body), content_type="application/json",
    )

    assert response
    assert response.status_code == status.HTTP_200_OK

    text = b"".join(list(response.streaming_content)).decode()  # type: ignore
    lines = text.split("\n")
    assert len(lines) == 5
    assert lines[0] == (
        "familyId\tpersonId\tmomId\tdadId\tsex\tstatus\trole\tsample_id\t"
        "layout\tgenerated\tnot_sequenced\ttag_nuclear_family\t"
        "tag_quad_family\ttag_trio_family\ttag_simplex_family\t"
        "tag_multiplex_family\ttag_control_family\ttag_affected_dad_family\t"
        "tag_affected_mom_family\ttag_affected_prb_family\t"
        "tag_affected_sib_family\ttag_unaffected_dad_family\t"
        "tag_unaffected_mom_family\ttag_unaffected_prb_family\t"
        "tag_unaffected_sib_family\ttag_male_prb_family\t"
        "tag_female_prb_family\ttag_missing_mom_family\t"
        "tag_missing_dad_family\tmember_index\tphenotype"
    )
    assert (
        "f2.1\tmom1\t0\t0\tF\tunaffected\tmom\tmom1\t1:10.0,50.0\t"
        "False\tFalse\tTrue\tFalse\tTrue\tTrue\tFalse\tFalse\tFalse\t"
        "False\tTrue\tFalse\tTrue\tTrue\tFalse\tFalse\tFalse\t"
        "True\tFalse\tFalse\t0\tunaffected"
    ) in lines
