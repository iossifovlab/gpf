# pylint: disable=W0621,C0114,C0116
import json
import pathlib
from typing import Any, cast

import pytest
import pytest_mock
from gain.genomic_resources.testing import setup_denovo, setup_pedigree

from gpf.configuration.gpf_config_parser import DefaultBox
from gpf.enrichment_tool.enrichment_cache_builder import (
    build_enrichment_event_counts_cache,
)
from gpf.enrichment_tool.enrichment_utils import (
    get_enrichment_cache_path,
    get_enrichment_config,
)
from gpf.gpf_instance import GPFInstance
from gpf.studies.study import GenotypeData
from gpf.testing.import_helpers import denovo_study


@pytest.fixture
def study_1(
    tmp_path: pathlib.Path,
    t4c8_fixture: GPFInstance,
) -> GenotypeData:
    ped_path = setup_pedigree(
        tmp_path / "input" / "ped_1" / "in.ped",
        """
familyId personId dadId momId sex status role
f1.1     mom1     0     0     2   1      mom
f1.1     dad1     0     0     1   1      dad
f1.1     ch1      dad1  mom1  2   2      prb
f1.3     mom3     0     0     2   1      mom
f1.3     dad3     0     0     1   1      dad
f1.3     ch3      dad3  mom3  2   2      prb
        """)
    denovo_path = setup_denovo(
        tmp_path / "input" / "denovo_1" / "denovo.tsv",
        """
chrom  pos  ref  alt  person_id
chr1   52   C    A    ch1
chr1   52   C    T    ch3
chr1   53   A    C    ch1
chr1   54   T    C    ch3
chr1   57   A    G    ch1
chr1   114  C    T    ch3
chr1   195  C    T    ch1
chr1   145  C    T    ch3
        """,
    )
    return denovo_study(
        tmp_path, "study_1", ped_path, [denovo_path],
        gpf_instance=t4c8_fixture,
        study_config_update={
            "enrichment": {
                "enabled": True,
                "selected_person_set_collections": ["status"],
                "effect_types": ["LGDs", "missense", "synonymous"],
            },
        })


def _cache_path(study: GenotypeData) -> pathlib.Path:
    return pathlib.Path(get_enrichment_cache_path(study))


def _read_cache(study: GenotypeData) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(_cache_path(study).read_text()))


def test_writes_cache_for_each_counter_person_set_and_effect_group(
    study_1: GenotypeData,
) -> None:
    build_enrichment_event_counts_cache(study_1, "status")

    cache = _read_cache(study_1)
    assert list(cache) == [
        "enrichment_events_counting", "enrichment_gene_counting",
    ]
    for counter_result in cache.values():
        assert list(counter_result) == ["affected", "unaffected"]
        for ps_result in counter_result.values():
            assert list(ps_result) == ["LGDs", "missense", "synonymous"]


def test_writes_cache_to_enrichment_cache_json_in_config_dir(
    study_1: GenotypeData,
) -> None:
    build_enrichment_event_counts_cache(study_1, "status")

    assert _cache_path(study_1) == (
        pathlib.Path(study_1.config_dir) / "enrichment_cache.json")
    assert _cache_path(study_1).exists()


def test_counts_events_of_affected_children(study_1: GenotypeData) -> None:
    build_enrichment_event_counts_cache(study_1, "status")

    affected = _read_cache(study_1)["enrichment_events_counting"]["affected"]
    assert affected == {
        "LGDs": {
            "all": 2, "rec": 1, "male": 0, "female": 2,
            "unspecified": 0, "rec_genes": None,
        },
        "missense": {
            "all": 2, "rec": 1, "male": 0, "female": 2,
            "unspecified": 0, "rec_genes": None,
        },
        "synonymous": {
            "all": 3, "rec": 1, "male": 0, "female": 3,
            "unspecified": 0, "rec_genes": None,
        },
    }


def test_counts_genes_of_affected_children(study_1: GenotypeData) -> None:
    build_enrichment_event_counts_cache(study_1, "status")

    affected = _read_cache(study_1)["enrichment_gene_counting"]["affected"]
    assert affected == {
        "LGDs": {
            "all": 1, "rec": 1, "male": 0, "female": 1,
            "unspecified": 0, "rec_genes": None,
        },
        "missense": {
            "all": 1, "rec": 1, "male": 0, "female": 1,
            "unspecified": 0, "rec_genes": None,
        },
        "synonymous": {
            "all": 2, "rec": 1, "male": 0, "female": 2,
            "unspecified": 0, "rec_genes": None,
        },
    }


def test_counts_zero_for_person_set_with_no_children(
    study_1: GenotypeData,
) -> None:
    zero = {
        "all": 0, "rec": 0, "male": 0, "female": 0,
        "unspecified": 0, "rec_genes": None,
    }

    build_enrichment_event_counts_cache(study_1, "status")

    cache = _read_cache(study_1)
    for counter_id in cache:
        assert cache[counter_id]["unaffected"] == {
            "LGDs": zero, "missense": zero, "synonymous": zero,
        }


def test_keeps_rec_genes_key_with_null_value_in_each_entry(
    study_1: GenotypeData,
) -> None:
    build_enrichment_event_counts_cache(study_1, "status")

    entries = [
        entry
        for counter_result in _read_cache(study_1).values()
        for ps_result in counter_result.values()
        for entry in ps_result.values()
    ]
    assert len(entries) == 12
    assert all(
        "rec_genes" in entry and entry["rec_genes"] is None
        for entry in entries)
    assert '"rec_genes": null' in _cache_path(study_1).read_text()


def test_writes_json_with_indent_4(study_1: GenotypeData) -> None:
    build_enrichment_event_counts_cache(study_1, "status")

    text = _cache_path(study_1).read_text()
    assert text == json.dumps(json.loads(text), indent=4)


def test_overwrites_existing_cache_file(study_1: GenotypeData) -> None:
    _cache_path(study_1).write_text("stale content")

    build_enrichment_event_counts_cache(study_1, "status")

    assert set(_read_cache(study_1)) == {
        "enrichment_events_counting", "enrichment_gene_counting",
    }


def test_queries_variants_once(
    study_1: GenotypeData,
    mocker: pytest_mock.MockerFixture,
) -> None:
    spy = mocker.spy(study_1, "query_variants")

    build_enrichment_event_counts_cache(study_1, "status")

    spy.assert_called_once()


def test_unknown_person_set_collection_raises_assertion_error(
    study_1: GenotypeData,
) -> None:
    with pytest.raises(AssertionError):
        build_enrichment_event_counts_cache(study_1, "no_such_psc")

    assert not _cache_path(study_1).exists()


@pytest.fixture
def study_without_enrichment(
    f1_trio: GenotypeData,
    mocker: pytest_mock.MockerFixture,
) -> GenotypeData:
    # The study config schema fills in a disabled `enrichment` section,
    # so drop the key to reach the early return.
    config = DefaultBox(f1_trio.config.to_dict())
    del config["enrichment"]
    mocker.patch.object(f1_trio, "config", config)
    return f1_trio


def test_study_without_enrichment_writes_no_cache(
    study_without_enrichment: GenotypeData,
) -> None:
    assert get_enrichment_config(study_without_enrichment) is None

    build_enrichment_event_counts_cache(study_without_enrichment, "phenotype")

    assert not _cache_path(study_without_enrichment).exists()


def test_study_without_enrichment_does_not_query_variants(
    study_without_enrichment: GenotypeData,
    mocker: pytest_mock.MockerFixture,
) -> None:
    spy = mocker.spy(study_without_enrichment, "query_variants")

    build_enrichment_event_counts_cache(study_without_enrichment, "phenotype")

    spy.assert_not_called()


def test_person_set_collection_check_runs_before_enrichment_check(
    study_without_enrichment: GenotypeData,
) -> None:
    with pytest.raises(AssertionError):
        build_enrichment_event_counts_cache(
            study_without_enrichment, "no_such_psc")
