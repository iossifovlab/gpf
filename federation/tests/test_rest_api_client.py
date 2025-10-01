# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.pheno.common import MeasureType
from requests import Response

from rest_client.rest_client import RESTClient


def test_get_datasets(rest_client: RESTClient) -> None:
    datasets = rest_client.get_datasets()
    assert datasets is not None
    assert isinstance(datasets, list)
    assert {dataset["id"] for dataset in datasets} == {
        "study_1_pheno",
        "t4c8_dataset",
        "t4c8_study_1",
        "t4c8_study_2",
        "t4c8_study_4",
    }


def test_get_variants_preview(rest_client: RESTClient) -> None:
    data = {"datasetId": "t4c8_study_1"}
    variants_response = rest_client.get_variants_preview(data)
    assert variants_response is not None
    assert isinstance(variants_response, Response)


def test_get_common_report(rest_client: RESTClient) -> None:
    common_report = rest_client.get_common_report("t4c8_study_1")
    assert common_report is not None
    assert isinstance(common_report, dict)
    assert common_report["id"] == "t4c8_study_1"
    assert common_report["people_report"][0]["columns"] == [
        "autism", "unaffected",
    ]


def test_get_common_report_families_data(rest_client: RESTClient) -> None:
    families_response = \
        rest_client.get_common_report_families_data("t4c8_study_1")

    assert families_response is not None
    assert isinstance(families_response, Response)


def test_get_common_report_families_data_columns(
    rest_client: RESTClient,
) -> None:
    families_response = \
        rest_client.get_common_report_families_data("t4c8_study_1")

    content = families_response.content.decode("utf-8").split("\n")
    assert families_response is not None
    first_row = content[0].split("\t")
    assert len(first_row) == 31


def test_get_browser_measures_info(rest_client: RESTClient) -> None:
    measures_info = rest_client.get_browser_measures_info("t4c8_study_1")

    assert measures_info is not None
    assert isinstance(measures_info, dict)


def test_get_instruments(rest_client: RESTClient) -> None:
    instruments = rest_client.get_instruments("t4c8_study_1")

    assert instruments is not None
    assert isinstance(instruments, list)


def test_post_enrichment_test(rest_client: RESTClient) -> None:
    data = {
        "datasetId": "t4c8_study_4",
        "geneSymbols": ["T4"],
    }
    response = rest_client.post_enrichment_test(data)

    assert response is not None
    assert isinstance(response, dict)


def test_get_instruments_details(rest_client: RESTClient) -> None:
    instrument_details = rest_client.get_instruments_details("t4c8_study_1")

    assert instrument_details is not None
    assert isinstance(instrument_details, dict)


def test_get_measure(rest_client: RESTClient) -> None:
    measure = rest_client.get_measure("t4c8_study_1", "i1.m1")

    assert measure is not None
    assert isinstance(measure, dict)


def test_get_measures(rest_client: RESTClient) -> None:
    measures = rest_client.get_measures(
        "t4c8_study_1", "i1", MeasureType.continuous)

    assert measures is not None
    assert isinstance(measures, list)


def test_post_measure_values(rest_client: RESTClient) -> None:
    measure_values = rest_client.post_measure_values(
        "t4c8_study_1", "i1.m1", None, None, None)

    assert measure_values is not None
    assert isinstance(measure_values, str)


def test_get_measures_download(rest_client: RESTClient) -> None:
    csv = rest_client.get_measures_download(
        "t4c8_study_1", search_term="i1.m1",
    )
    lines = list(csv)

    assert lines is not None
    print(b"".join(lines).decode())
    assert len(lines) == 386


def test_post_pheno_tool(rest_client: RESTClient) -> None:
    data = {
        "datasetId": "t4c8_study_1",
        "measureId": "i1.m1",
        "normalizeBy": [{
            "display_name": "Non Verbal IQ",
            "instrument_name": "i1",
            "measure_name": "iq",
        }],
        "presentInParent": {
            "presentInParent": ["neither"],
            "rarity": {
                "ultraRare": True,
                "minFreq": None,
                "maxFreq": None,
            },
        },
        "effectTypes": ["LGDs", "Missense", "Synonymous"],
    }
    test_results = rest_client.post_pheno_tool(data)

    assert test_results is not None
    assert isinstance(test_results, dict)


def test_roles_list(rest_client: RESTClient) -> None:
    test_results = rest_client.get_pheno_roles("t4c8_study_1")
    assert test_results == ["dad", "mom", "prb", "sib"]
