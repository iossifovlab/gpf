# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pathlib
import pytest
from pytest_mock import MockerFixture

from box import Box

from dae.testing.alla_import import alla_gpf

from dae.gpf_instance import GPFInstance
from dae.gene.gene_sets_db import GeneSet
from dae.autism_gene_profile.statistic import AGPStatistic
from dae.autism_gene_profile.db import AutismGeneProfileDB


@pytest.fixture
def agp_config() -> Box:
    return Box({
        "gene_sets": [
            {
                "category": "relevant_gene_sets",
                "display_name": "Relevant Gene Sets",
                "sets": [
                    {"set_id": "CHD8 target genes", "collection_id": "main"},
                    {
                        "set_id": "FMRP Darnell",
                        "collection_id": "main"
                    }
                ]
            },
        ],
        "genomic_scores": [
            {
                "category": "protection_scores",
                "display_name": "Protection scores",
                "scores": [
                    {"score_name": "SFARI gene score", "format": "%s"},
                    {"score_name": "RVIS_rank", "format": "%s"},
                    {"score_name": "RVIS", "format": "%s"}
                ]
            },
            {
                "category": "autism_scores",
                "display_name": "Autism scores",
                "scores": [
                    {"score_name": "SFARI gene score", "format": "%s"},
                    {"score_name": "RVIS_rank", "format": "%s"},
                    {"score_name": "RVIS", "format": "%s"}
                ]
            },
        ],
        "datasets": Box({
            "iossifov_2014": Box({
                "statistics": [
                    {
                        "id": "denovo_noncoding",
                        "display_name": "Noncoding",
                        "effects": ["noncoding"],
                        "category": "denovo"
                    },
                    {
                        "id": "denovo_missense",
                        "display_name": "Missense",
                        "effects": ["missense"],
                        "category": "denovo"
                    }
                ],
                "person_sets": [
                    {
                        "set_name": "autism",
                        "collection_name": "phenotype"
                    },
                    {
                        "set_name": "unaffected",
                        "collection_name": "phenotype"
                    },
                ]
            })
        })
    })


@pytest.fixture
def sample_agp() -> AGPStatistic:
    gene_sets = ["main_CHD8 target genes"]
    genomic_scores = {
        "protection_scores": {
            "SFARI gene score": 1, "RVIS_rank": 193.0, "RVIS": -2.34
        },
        "autism_scores": {
            "SFARI gene score": 1, "RVIS_rank": 193.0, "RVIS": -2.34
        },
    }
    variant_counts = {
        "iossifov_2014": {
            "autism": {
                "denovo_noncoding": {"count": 53, "rate": 1},
                "denovo_missense": {"count": 21, "rate": 2}
            },
            "unaffected": {
                "denovo_noncoding": {"count": 43, "rate": 3},
                "denovo_missense": {"count": 51, "rate": 4}
            },
        }
    }
    return AGPStatistic(
        "CHD8", gene_sets, genomic_scores, variant_counts
    )


@pytest.fixture
def agp_gpf_instance(
        tmp_path: pathlib.Path,
        agp_config: Box,
        sample_agp: AGPStatistic,
        mocker: MockerFixture) -> GPFInstance:
    root_path = tmp_path
    gpf_instance = alla_gpf(root_path)
    agpdb_filename = str(root_path / "agpdb")

    mocker.patch.object(
        GPFInstance,
        "_autism_gene_profile_config",
        return_value=agp_config,
        new_callable=mocker.PropertyMock
    )
    main_gene_sets = {
        "autism candidates",
    }
    mocker.patch.object(
        gpf_instance.gene_sets_db,
        "get_gene_set_ids",
        return_value=main_gene_sets
    )

    mocker.patch.object(
        gpf_instance.gene_sets_db,
        "get_gene_set",
        return_value=GeneSet(
            "autism candidates",
            "autism candidates",
            ["CHD8"]))

    gpf_instance._autism_gene_profile_db = \
        AutismGeneProfileDB(
            gpf_instance._autism_gene_profile_config,
            agpdb_filename,
            clear=True
        )
    print(agpdb_filename)
    gpf_instance._autism_gene_profile_db.insert_agp(sample_agp)

    return gpf_instance


@pytest.fixture
def local_gpf_instance(
        tmp_path: pathlib.Path,
        agp_config: Box,
        sample_agp: AGPStatistic,
        mocker: MockerFixture) -> GPFInstance:
    root_path = tmp_path
    gpf_instance = GPFInstance.build(
        os.path.join(
            os.path.dirname(__file__),
            "../../../../data/data-hg19-local/gpf_instance.yaml"))
    agpdb_filename = str(root_path / "agpdb")

    mocker.patch.object(
        GPFInstance,
        "_autism_gene_profile_config",
        return_value=agp_config,
        new_callable=mocker.PropertyMock
    )
    main_gene_sets = {
        "CHD8 target genes",
        "FMRP Darnell",
        "FMRP Tuschl",
        "PSD",
        "autism candidates from Iossifov PNAS 2015",
        "autism candidates from Sanders Neuron 2015",
        "brain critical genes",
        "brain embryonically expressed",
        "chromatin modifiers",
        "essential genes",
        "non-essential genes",
        "postsynaptic inhibition",
        "synaptic clefts excitatory",
        "synaptic clefts inhibitory",
        "topotecan downreg genes"
    }
    mocker.patch.object(
        gpf_instance.gene_sets_db,
        "get_gene_set_ids",
        return_value=main_gene_sets
    )
    gpf_instance._autism_gene_profile_db = \
        AutismGeneProfileDB(
            gpf_instance._autism_gene_profile_config,
            agpdb_filename,
            clear=True
        )
    print(agpdb_filename)
    gpf_instance._autism_gene_profile_db.insert_agp(sample_agp)

    return gpf_instance
