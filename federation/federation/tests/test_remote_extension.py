# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from gpf_instance.gpf_instance import WGPFInstance
from studies.study_wrapper import WDAEStudy, WDAEStudyGroup

from federation.remote_extension import GPFRemoteExtension
from federation.remote_pheno_tool_adapter import RemotePhenoToolAdapter
from federation.remote_study_wrapper import (
    RemoteWDAEStudy,
    RemoteWDAEStudyGroup,
)
from federation.rest_api_client import RESTClient


def test_get_available_data_ids(t4c8_instance: WGPFInstance) -> None:
    expected_ids = {
        "t4c8_dataset", "t4c8_study_1", "TEST_REMOTE_t4c8_dataset",
        "TEST_REMOTE_t4c8_study_1", "t4c8_study_2", "TEST_REMOTE_t4c8_study_4",
        "study_1_pheno", "TEST_REMOTE_t4c8_study_2",
        "TEST_REMOTE_study_1_pheno", "t4c8_study_4",
    }

    actual_ids = set(t4c8_instance.get_available_data_ids())
    assert actual_ids == expected_ids


def test_get_wdae_wrapper(t4c8_instance: WGPFInstance) -> None:
    for study_id in [
        "t4c8_dataset",
        "t4c8_study_1",
        "t4c8_study_2",
        "study_1_pheno",
        "t4c8_study_4",
    ]:
        assert isinstance(
            t4c8_instance.get_wdae_wrapper(study_id),
            (WDAEStudyGroup, WDAEStudy),
        ) is True

    for study_id in [
        "TEST_REMOTE_t4c8_dataset",
        "TEST_REMOTE_t4c8_study_1",
        "TEST_REMOTE_t4c8_study_4",
        "TEST_REMOTE_t4c8_study_2",
        "TEST_REMOTE_study_1_pheno",
    ]:
        assert isinstance(
            t4c8_instance.get_wdae_wrapper(study_id),
            (RemoteWDAEStudy, RemoteWDAEStudyGroup),
        ) is True


def test_extension_get_studies_ids(
    test_remote_extension: GPFRemoteExtension,
) -> None:
    expected_studies = {
        "TEST_REMOTE_t4c8_study_2",
        "TEST_REMOTE_t4c8_study_1",
        "TEST_REMOTE_t4c8_dataset",
        "TEST_REMOTE_study_1_pheno",
        "TEST_REMOTE_t4c8_study_4",
    }

    returned_studies = set(test_remote_extension.get_studies_ids())
    assert returned_studies == expected_studies

    study = test_remote_extension.studies.get("TEST_REMOTE_t4c8_study_1")
    assert study is not None

    tool = test_remote_extension.get_tool(study, "pheno_tool")
    assert tool is not None


def test_extension_get_tool(
    t4c8_instance: WGPFInstance,
    test_remote_extension: GPFRemoteExtension,
) -> None:
    study = t4c8_instance.get_wdae_wrapper("t4c8_study_4")
    tool = test_remote_extension.get_tool(study, "pheno_tool")
    assert tool is None

    study = t4c8_instance.get_wdae_wrapper("TEST_REMOTE_t4c8_study_1")
    tool = test_remote_extension.get_tool(study, "pheno_tool")
    assert tool is not None


def test_extension_get_tool_unsupported_tool(
    t4c8_instance: WGPFInstance,
    test_remote_extension: GPFRemoteExtension,
) -> None:
    study = t4c8_instance.get_wdae_wrapper("TEST_REMOTE_t4c8_study_1")

    tool = test_remote_extension.get_tool(study, "pheno_tool")
    assert tool is not None

    tool = test_remote_extension.get_tool(study, "unsupported-tool")
    assert tool is None


def test_pheno_tool_calc_variants(
    rest_client: RESTClient,
    t4c8_instance: WGPFInstance,  # noqa: ARG001
) -> None:
    query = {
        "datasetId": "t4c8_study_1",
        "measureId": "i1.m1",
        "normalizeBy": [],
        "effectTypes": ["missense", "frame-shift", "synonymous"],
        "presentInParent": {"presentInParent": ["neither"]},
    }

    adapter = RemotePhenoToolAdapter(rest_client, "t4c8_study_1")
    result = adapter.calc_variants(query)

    assert result["description"] == "i1.m1"
    effects = {r["effect"] for r in result["results"]}
    assert effects == {"missense", "frame-shift", "synonymous"}

    missense = next(r for r in result["results"] if r["effect"] == "missense")
    assert missense["femaleResults"]["positive"]["count"] == 1
    assert missense["femaleResults"]["positive"]["mean"] == \
        pytest.approx(110.71112823486328, abs=1e-3)
    assert missense["femaleResults"]["negative"]["count"] == 1
    assert missense["femaleResults"]["negative"]["mean"] == \
        pytest.approx(96.634521484375, abs=1e-3)

    frameshift = next(
        r for r in result["results"] if r["effect"] == "frame-shift")
    assert frameshift["femaleResults"]["negative"]["count"] == 2
    assert frameshift["femaleResults"]["negative"]["mean"] == \
        pytest.approx(103.67282485961914, abs=1e-3)

    synonymous = next(
        r for r in result["results"] if r["effect"] == "synonymous")
    assert synonymous["femaleResults"]["positive"]["count"] == 1
    assert synonymous["femaleResults"]["positive"]["mean"] == \
        pytest.approx(96.634521484375, abs=1e-3)
    assert synonymous["femaleResults"]["negative"]["count"] == 1
    assert synonymous["femaleResults"]["negative"]["mean"] == \
        pytest.approx(110.71112823486328, abs=1e-3)
