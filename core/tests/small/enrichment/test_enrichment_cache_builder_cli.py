# pylint: disable=W0621,C0114,C0116,C0115,R0903
from typing import Any, cast

import pytest
import pytest_mock

from gpf.enrichment_tool import enrichment_cache_builder
from gpf.enrichment_tool.enrichment_cache_builder import cli
from gpf.gpf_instance import GPFInstance


def test_help_exits_with_code_zero() -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli(["--help"])

    assert exc_info.value.code == 0


def test_unknown_option_exits_with_code_two() -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli(["--no-such-option"])

    assert exc_info.value.code == 2


class StubStudy:
    def __init__(
        self, study_id: str, enrichment: dict[str, Any] | None,
    ) -> None:
        self.study_id = study_id
        self.config: dict[str, Any] = {}
        if enrichment is not None:
            self.config["enrichment"] = enrichment


class StubGPFInstance:
    def __init__(self, studies: list[StubStudy]) -> None:
        self._studies = {study.study_id: study for study in studies}

    def get_all_genotype_data(self) -> list[StubStudy]:
        return list(self._studies.values())

    def get_genotype_data_ids(self) -> list[str]:
        return list(self._studies)

    def get_genotype_data(self, study_id: str) -> StubStudy | None:
        return self._studies.get(study_id)


def _enrichment(
    *psc_ids: str, enabled: bool = True,
) -> dict[str, Any]:
    return {
        "enabled": enabled,
        "selected_person_set_collections": list(psc_ids),
    }


@pytest.fixture
def stub_instance() -> StubGPFInstance:
    return StubGPFInstance([
        StubStudy("study_a", _enrichment("phenotype", "status")),
        StubStudy("study_b", _enrichment("status", enabled=False)),
        StubStudy("study_c", None),
    ])


@pytest.fixture
def build_cache(mocker: pytest_mock.MockerFixture) -> Any:
    return mocker.patch.object(
        enrichment_cache_builder, "build_enrichment_event_counts_cache")


def _gpf(instance: StubGPFInstance) -> GPFInstance:
    return cast(GPFInstance, instance)


def _built(build_cache: Any) -> list[tuple[str, str]]:
    return [
        (call.args[0].study_id, call.args[1])
        for call in build_cache.call_args_list
    ]


def test_show_studies_prints_studies_with_enrichment_section(
    stub_instance: StubGPFInstance,
    build_cache: Any,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cli(["--show-studies"], gpf_instance=_gpf(stub_instance))

    assert capsys.readouterr().out.splitlines() == ["study_a", "study_b"]
    build_cache.assert_not_called()


def test_default_builds_cache_of_each_study_with_enrichment_section(
    stub_instance: StubGPFInstance,
    build_cache: Any,
) -> None:
    cli([], gpf_instance=_gpf(stub_instance))

    assert _built(build_cache) == [
        ("study_a", "phenotype"), ("study_b", "status")]


def test_studies_option_selects_the_listed_studies(
    stub_instance: StubGPFInstance,
    build_cache: Any,
) -> None:
    cli(
        ["--studies", "study_b,study_c"],
        gpf_instance=_gpf(stub_instance))

    assert _built(build_cache) == [("study_b", "status")]


def test_unknown_study_id_raises_attribute_error(
    stub_instance: StubGPFInstance,
    build_cache: Any,
) -> None:
    with pytest.raises(AttributeError):
        cli(
            ["--studies", "no_such_study"],
            gpf_instance=_gpf(stub_instance))

    build_cache.assert_not_called()


def test_empty_selected_person_set_collections_raises_index_error(
    build_cache: Any,
) -> None:
    instance = StubGPFInstance([StubStudy("study_e", _enrichment())])

    with pytest.raises(IndexError):
        cli([], gpf_instance=_gpf(instance))

    build_cache.assert_not_called()


def test_missing_gpf_instance_builds_one(
    mocker: pytest_mock.MockerFixture,
    stub_instance: StubGPFInstance,
    build_cache: Any,
) -> None:
    build = mocker.patch.object(
        GPFInstance, "build", return_value=stub_instance)

    cli(["--studies", "study_a"])

    build.assert_called_once_with()
    assert _built(build_cache) == [("study_a", "phenotype")]
