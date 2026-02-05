# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

import pytest
import yaml
from box import Box
from dae.gene_profile.generate_gene_profile import main as gp_main
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import (
    setup_directories,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.utils.testing import (
    setup_t4c8_grr,
    setup_t4c8_instance,
)


@pytest.fixture(scope="module")
def gp_grr(
    tmp_path_factory: pytest.TempPathFactory,
) -> GenomicResourceRepo:
    root_path = tmp_path_factory.mktemp(
        "test_generate_gene_profiles_internals_gp_grr")
    setup_directories(
        root_path, {
            "gene_sets": {
                "genomic_resource.yaml": textwrap.dedent("""
                    type: gene_set_collection
                    id: gene_sets
                    format: directory
                    directory: test_gene_sets
                    web_label: test gene sets
                    web_format_str: "key| (|count|): |desc"
                """),
                "test_gene_sets": {
                    "test_gene_set_1.txt": textwrap.dedent("""
                        test_gene_set_1
                        contains t4
                        t4
                    """),
                    "test_gene_set_2.txt": textwrap.dedent("""
                        test_gene_set_2
                        contains c8
                        c8
                    """),
                    "test_gene_set_3.txt": textwrap.dedent("""
                        test_gene_set_3
                        contains t4 and c8
                        t4
                        c8
                    """),
                },
            },
            "gene_score1": {
                "genomic_resource.yaml": textwrap.dedent("""
                    type: gene_score
                    filename: score.csv
                    scores:
                    - id: gene_score1
                      desc: Test gene score
                      histogram:
                        type: number
                        number_of_bins: 100
                        view_range:
                            min: 0.0
                            max: 30.0
                """),
                "score.csv": textwrap.dedent("""
                    gene,gene_score1
                    t4,10
                    c8,20
                """),
            },
        },
    )
    return setup_t4c8_grr(root_path)


@pytest.fixture(scope="module")
def gp_config() -> dict:
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
            "t4c8_dataset",
        ],
        "default_dataset": "t4c8_dataset",
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
            "t4c8_dataset": {
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
                    {
                        "id": "rare_lgds",
                        "display_name": "rare LGDs",
                        "effects": ["LGDs"],
                        "category": "rare",
                    },
                    {
                        "id": "rare_missense",
                        "display_name": "rare missense",
                        "effects": ["missense"],
                        "category": "rare",
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


@pytest.fixture(scope="module")
def gp_t4c8_instance(
    tmp_path_factory: pytest.TempPathFactory,
    gp_grr: GenomicResourceRepo,
    gp_config: Box,
) -> GPFInstance:
    root_path = tmp_path_factory.mktemp(
        "test_generate_gene_profiles_internals_gp_instance")
    instance_path = root_path / "gpf_instance"
    assert gp_grr is not None
    assert gp_grr.definition is not None

    setup_directories(
        instance_path, {
            "gpf_instance.yaml": textwrap.dedent(f"""
                instance_id: t4c8_instance
                grr:
                    type: {gp_grr.definition['type']}
                    id: {gp_grr.definition['id']}
                    directory: {gp_grr.definition['directory']}
                reference_genome:
                  resource_id: t4c8_genome
                gene_models:
                  resource_id: t4c8_genes
                gene_sets_db:
                  gene_set_collections:
                  - gene_sets
                gene_scores_db:
                  gene_scores:
                  - "gene_scores/t4c8_score"
                  - gene_score1
                gene_profiles_config:
                  conf_file: "gp_config.yaml"
                default_study_config:
                  conf_file: default_study_configuration.yaml
                genotype_storage:
                  default: duckdb_gpf_test
                  storages:
                  - id: duckdb_gpf_test
                    storage_type: duckdb_parquet
                    memory_limit: 16GB
                    base_dir: '%(wd)s/duckdb_storage'
                gpfjs:
                  visible_datasets:
                  - t4c8_dataset
                  - t4c8_study_1
                  - nonexistent_dataset
            """),
        },
    )

    (instance_path / "gp_config.yaml").write_text(yaml.safe_dump(gp_config))

    return setup_t4c8_instance(
        root_path,
        grr=gp_grr,
    )


def test_generate_gene_profile_internals(
    gp_t4c8_instance: GPFInstance,
    tmp_path: pathlib.Path,
) -> None:
    assert gp_t4c8_instance is not None
    # pylint: disable=protected-access, invalid-name
    gp_config = gp_t4c8_instance._gene_profile_config
    assert gp_config is not None

    gpdb_path = tmp_path / "gpdb.duckdb"
    argv = [
        "--dbfile",
        str(gpdb_path),
        "-vv",
        "-j", "1",
        "--no-split",
    ]

    gp_main(gp_t4c8_instance, argv)
    assert gpdb_path.exists()
