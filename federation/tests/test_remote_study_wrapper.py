# pylint: disable=W0621,C0114,C0116,W0212,W0613
from federation.remote_study_wrapper import (
    RemoteWDAEStudy,
    handle_denovo_gene_sets,
    handle_gene_sets,
    handle_genomic_scores,
)
from gpf_instance.gpf_instance import WGPFInstance
from studies.query_transformer import QueryTransformer
from studies.response_transformer import ResponseTransformer


def test_query_variants_wdae_remote_study_filters(
    t4c8_wgpf_instance: WGPFInstance,
    t4c8_query_transformer: QueryTransformer,
    t4c8_response_transformer: ResponseTransformer,
) -> None:
    remote_study = t4c8_wgpf_instance.get_wdae_wrapper(
        "TEST_REMOTE_t4c8_study_1")
    assert remote_study is not None
    assert isinstance(remote_study, RemoteWDAEStudy)

    query = {}
    result = list(remote_study.query_variants_preview_wdae(
        query, t4c8_query_transformer, t4c8_response_transformer))
    assert len(result) == 12

    query = {"study_filters": ["t4c8_study_1", "t4c8_study_2"]}
    result = list(remote_study.query_variants_preview_wdae(
        query, t4c8_query_transformer, t4c8_response_transformer))
    assert len(result) == 12


def test_get_measures_json(t4c8_wgpf_instance: WGPFInstance) -> None:
    remote_study = t4c8_wgpf_instance.get_wdae_wrapper(
        "TEST_REMOTE_t4c8_study_1")
    assert remote_study is not None
    assert isinstance(remote_study, RemoteWDAEStudy)

    result = remote_study.get_measures_json(["continuous", "categorical"])
    assert result is not None
    assert len(result) == 7


def test_query_gene_view_summary_variants_with_allowed_studies(
    t4c8_wgpf_instance: WGPFInstance,
    t4c8_query_transformer: QueryTransformer,
) -> None:
    filters = {
        "geneSymbols": ["t4"],
        "allowed_studies": ["t4c8_study_1"],
    }
    remote_study = t4c8_wgpf_instance.get_wdae_wrapper(
        "TEST_REMOTE_t4c8_dataset")
    assert remote_study is not None
    assert isinstance(remote_study, RemoteWDAEStudy)

    gen = remote_study._query_gene_view_summary_variants(
        t4c8_query_transformer, **filters)
    result = list(gen)
    assert len(result) == 3


def test_query_gene_view_summary_variants_with_study_filters(
    t4c8_wgpf_instance: WGPFInstance,
    t4c8_query_transformer: QueryTransformer,
) -> None:
    filters = {
        "geneSymbols": ["t4"],
        "studyFilters": ["t4c8_study_1"],
    }
    remote_study = t4c8_wgpf_instance.get_wdae_wrapper(
        "TEST_REMOTE_t4c8_dataset")
    assert remote_study is not None
    assert isinstance(remote_study, RemoteWDAEStudy)

    gen = remote_study._query_gene_view_summary_variants(
        t4c8_query_transformer, **filters)
    result = list(gen)
    assert len(result) == 3


def test_query_gene_view_summary_variants_allowed_studies_and_study_filters(
    t4c8_wgpf_instance: WGPFInstance,
    t4c8_query_transformer: QueryTransformer,
) -> None:
    filters = {
        "geneSymbols": ["t4"],
        "allowed_studies": ["t4c8_study_1", "t4c8_study_2"],
        "studyFilters": ["t4c8_study_1", "t4c8_study_4"],
    }
    remote_study = t4c8_wgpf_instance.get_wdae_wrapper(
        "TEST_REMOTE_t4c8_dataset")
    assert remote_study is not None
    assert isinstance(remote_study, RemoteWDAEStudy)

    gen = remote_study._query_gene_view_summary_variants(
        t4c8_query_transformer, **filters)
    result = list(gen)
    assert len(result) == 3


def test_handling_of_denovo_gene_sets(
    t4c8_wgpf_instance: WGPFInstance,
) -> None:
    query = {
        "datasetId": "TEST_REMOTE_t4c8_study_1",
        "geneSet": {
            "geneSet": "Missense",
            "geneSetsCollection": "denovo",
            "geneSetsTypes": [{
                "datasetId": "TEST_REMOTE_t4c8_study_1",
                "collections":  [
                    {"personSetId": "phenotype", "types": ["autism"]},
                ],
            }],
        },
    }

    remote_study = t4c8_wgpf_instance.get_wdae_wrapper(
        "TEST_REMOTE_t4c8_dataset")
    assert remote_study is not None
    assert isinstance(remote_study, RemoteWDAEStudy)

    handle_denovo_gene_sets(remote_study.rest_client, query)
    assert query is not None
    assert query == {
        "datasetId": "TEST_REMOTE_t4c8_study_1",
        "geneSet": {
            "geneSet": "Missense",
            "geneSetsCollection": "denovo",
            "geneSetsTypes": [{
                "datasetId": "t4c8_study_1",  # Removed prefix
                "collections":  [
                    {"personSetId": "phenotype", "types": ["autism"]},
                ],
            }],
        },
    }


def test_handling_of_gene_sets(
    t4c8_wgpf_instance: WGPFInstance,
) -> None:
    query = {
        "datasetId": "TEST_REMOTE_t4c8_study_1",
        "geneSet": {
            "geneSetsCollection": "TEST_REMOTE_main",
            "geneSet": "t4_candidates",
            "geneSetsTypes": [],
        },
    }

    remote_study = t4c8_wgpf_instance.get_wdae_wrapper(
        "TEST_REMOTE_t4c8_dataset")
    assert remote_study is not None
    assert isinstance(remote_study, RemoteWDAEStudy)

    handle_gene_sets(remote_study.rest_client, query)
    assert query is not None
    assert query == {
        "datasetId": "TEST_REMOTE_t4c8_study_1",
        "geneSet": {
            "geneSetsCollection": "main",  # Removed prefix
            "geneSet": "t4_candidates",
            "geneSetsTypes": [],
        },
    }


def test_handling_of_genomic_scores(
    t4c8_wgpf_instance: WGPFInstance,
) -> None:
    query = {
        "datasetId": "TEST_REMOTE_t4c8_study_1",
        "genomicScores": [
            {
                "categoricalView": None,
                "histogramType": "continuous",
                "rangeEnd": 99,
                "rangeStart": 50,
                "score": "TEST_REMOTE_score_one",
                "values": None,
            },
        ],
    }

    remote_study = t4c8_wgpf_instance.get_wdae_wrapper(
        "TEST_REMOTE_t4c8_dataset")
    assert remote_study is not None
    assert isinstance(remote_study, RemoteWDAEStudy)

    handle_genomic_scores(remote_study.rest_client, query)
    assert query is not None
    assert query == {
        "datasetId": "TEST_REMOTE_t4c8_study_1",
        "genomicScores": [
            {
                "categoricalView": None,
                "histogramType": "continuous",
                "rangeEnd": 99,
                "rangeStart": 50,
                "score": "score_one",
                "values": None,
            },
        ],
    }
