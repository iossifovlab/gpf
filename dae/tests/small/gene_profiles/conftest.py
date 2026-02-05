# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest
from box import Box
from dae.gene_profile.db import GeneProfileDB, GeneProfileDBWriter
from dae.gene_profile.statistic import GPStatistic
from dae.gene_sets.gene_sets_db import GeneSet
from dae.gpf_instance import GPFInstance
from dae.testing.alla_import import alla_gpf
from pytest_mock import MockerFixture


@pytest.fixture
def gp_config_1() -> dict:
    return {
        "gene_links": [
            {
                "name": "Link with prefix",
                "url": "{gpf_prefix}/datasets/{gene}",
            },
            {
                "name": "Link with gene info",
                "url": (
                    "https://site.com/{gene}?db={genome}&"
                    "position={chromosome_prefix}{chromosome}"
                    "/{gene_start_position}-{gene_stop_position}"
                ),
            },
        ],
        "order": [
            "gene_set_rank",
            "gene_score",
            "study_1",
        ],
        "default_dataset": "study_1",
        "gene_sets": [
            {
                "category": "gene_set",
                "display_name": "test gene sets",
                "sets": [
                    {
                        "set_id": "test_gene_set_1",
                        "collection_id": "gene_sets",
                    },
                    {
                        "set_id": "test_gene_set_2",
                        "collection_id": "gene_sets",
                    },
                    {
                        "set_id": "test_gene_set_3",
                        "collection_id": "gene_sets",
                    },
                ],
            },
        ],
        "gene_scores": [
            {
                "category": "gene_score",
                "display_name": "Test gene score",
                "scores": [
                    {"score_name": "gene_score1", "format": "%%s"},
                ],
            },
        ],
        "datasets": {
            "study_1": {
                "statistics": [
                    {
                        "id": "lgds",
                        "display_name": "LGDs",
                        "effects": ["LGDs"],
                        "category": "denovo",
                    },
                    {
                        "id": "denovo_missense",
                        "display_name": "missense",
                        "effects": ["missense"],
                        "category": "denovo",
                    },
                ],
                "person_sets": [
                    {
                        "set_name": "autism",
                        "collection_name": "phenotype",
                    },
                    {
                        "set_name": "unaffected",
                        "collection_name": "phenotype",
                    },
                ],
            },
        },
    }


@pytest.fixture
def gp_config() -> Box:
    return Box({
        "gene_sets": [
            {
                "category": "relevant_gene_sets",
                "display_name": "Relevant Gene Sets",
                "sets": [
                    {"set_id": "CHD8 target genes", "collection_id": "main"},
                    {
                        "set_id": "FMRP Darnell",
                        "collection_id": "main",
                    },
                ],
            },
        ],
        "gene_scores": [
            {
                "category": "protection_scores",
                "display_name": "Protection scores",
                "scores": [
                    {"score_name": "SFARI gene score", "format": "%s"},
                    {"score_name": "RVIS_rank", "format": "%s"},
                    {"score_name": "RVIS", "format": "%s"},
                ],
            },
            {
                "category": "autism_scores",
                "display_name": "Autism scores",
                "scores": [
                    {"score_name": "SFARI gene score", "format": "%s"},
                    {"score_name": "RVIS_rank", "format": "%s"},
                    {"score_name": "RVIS", "format": "%s"},
                ],
            },
        ],
        "datasets": Box({
            "iossifov_2014": Box({
                "statistics": [
                    {
                        "id": "denovo_noncoding",
                        "display_name": "Noncoding",
                        "effects": ["noncoding"],
                        "category": "denovo",
                    },
                    {
                        "id": "denovo_missense",
                        "display_name": "Missense",
                        "effects": ["missense"],
                        "category": "denovo",
                    },
                ],
                "person_sets": [
                    {
                        "set_name": "autism",
                        "collection_name": "phenotype",
                    },
                    {
                        "set_name": "unaffected",
                        "collection_name": "phenotype",
                    },
                ],
            }),
        }),
    })


@pytest.fixture
def sample_gp() -> GPStatistic:
    gene_sets = ["main_CHD8 target genes"]
    gene_scores = {
        "protection_scores": {
            "SFARI gene score": 1, "RVIS_rank": 193.0, "RVIS": -2.34,
        },
        "autism_scores": {
            "SFARI gene score": 1, "RVIS_rank": 193.0, "RVIS": -2.34,
        },
    }
    variant_counts = {
        "iossifov_2014_autism_denovo_noncoding": 53,
        "iossifov_2014_autism_denovo_noncoding_rate": 1,
        "iossifov_2014_autism_denovo_missense": 21,
        "iossifov_2014_autism_denovo_missense_rate": 2,
        "iossifov_2014_unaffected_denovo_noncoding": 43,
        "iossifov_2014_unaffected_denovo_noncoding_rate": 3,
        "iossifov_2014_unaffected_denovo_missense": 51,
        "iossifov_2014_unaffected_denovo_missense_rate": 4,
    }
    return GPStatistic(
        "CHD8", gene_sets, gene_scores, variant_counts,
    )


@pytest.fixture
def gp_gpf_instance(
        tmp_path: pathlib.Path,
        gp_config: Box,
        sample_gp: GPStatistic,  # noqa: ARG001
        mocker: MockerFixture) -> GPFInstance:
    root_path = tmp_path
    gpf_instance = alla_gpf(root_path)
    gpdb_filename = str(root_path / "gpdb")

    mocker.patch.object(
        GPFInstance,
        "_gene_profile_config",
        return_value=gp_config,
        new_callable=mocker.PropertyMock,
    )
    main_gene_sets = {
        "autism candidates",
    }
    mocker.patch.object(
        gpf_instance.gene_sets_db,
        "get_gene_set_ids",
        return_value=main_gene_sets,
    )

    mocker.patch.object(
        gpf_instance.gene_sets_db,
        "get_gene_set",
        return_value=GeneSet(
            "autism candidates",
            "autism candidates",
            ["CHD8"]))

    gpf_instance._gene_profile_db = GeneProfileDB(  # noqa: SLF001
            gpf_instance._gene_profile_config,  # noqa: SLF001
            gpdb_filename,
        )
    print(gpdb_filename)

    return gpf_instance


@pytest.fixture
def gpdb_write(
        tmp_path: pathlib.Path,
        gp_config: Box) -> GeneProfileDBWriter:
    gpdb_filename = str(tmp_path / "gpdb")
    return GeneProfileDBWriter(gp_config, gpdb_filename)
