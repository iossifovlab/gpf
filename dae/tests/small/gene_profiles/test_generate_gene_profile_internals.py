# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

import duckdb
import pytest
import pytest_mock
import yaml
from box import Box
from dae.gene_profile.generate_gene_profile import (
    GeneProfileDBWriter,
    _calculate_variant_counts,
    _collect_person_set_collections,
    _init_variant_counts,
    _merge_variant_counts,
    build_partitions,
    collect_variant_counts,
    merge_rare_queries,
)
from dae.gene_profile.generate_gene_profile import (
    main as gp_main,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import (
    setup_directories,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.utils.regions import Region
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
def gp_config() -> Box:
    return Box({
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
            "t4c8_study_3",
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
                        "id": "denovo_lgds",
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
                    {
                        "id": "rare_score_one_06",
                        "display_name": "rare big score one",
                        "genomic_scores": [{
                           "name": "score_one",
                           "min": 0.06,
                        }],
                        "category": "rare",
                    },
                ],
                "person_sets": [
                    {
                        "set_name": "autism",
                        "collection_name": "phenotype",
                    },
                    {
                        "set_name": "epilepsy",
                        "collection_name": "phenotype",
                    },
                    {
                        "set_name": "unaffected",
                        "collection_name": "phenotype",
                    },
                ],
            },
            "t4c8_study_3": {
                "statistics": [
                    {
                        "id": "denovo_lgds",
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
                    {
                        "id": "rare_score_one_06",
                        "display_name": "rare big score one",
                        "genomic_scores": [{
                           "name": "score_one",
                           "min": 0.06,
                        }],
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
    })


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
                    type: {gp_grr.definition["type"]}
                    id: {gp_grr.definition["id"]}
                    directory: {gp_grr.definition["directory"]}
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
                annotation:
                    conf_file: 'annotation.yaml'
                default_study_config:
                  conf_file: default_study_configuration.yaml
                genotype_storage:
                  default: duckdb_gpf_test
                  storages:
                  - id: duckdb_gpf_test
                    storage_type: duckdb_parquet
                    memory_limit: 16GB
                    base_dir: "%(wd)s/duckdb_storage"
                gpfjs:
                  visible_datasets:
                  - t4c8_dataset
                  - t4c8_study_1
                  - nonexistent_dataset
            """),
            "annotation.yaml": textwrap.dedent("""
                - position_score: genomic_scores/score_one
            """),
        },
    )

    (instance_path / "gp_config.yaml").write_text(
        yaml.safe_dump(gp_config.to_dict()))

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

    gpdb = GeneProfileDBWriter(gp_config, str(gpdb_path))

    cols = []
    with duckdb.connect(str(gpdb_path), read_only=True) as connection:
        cols = [
            row["column_name"] for row in connection.execute(
                f"DESCRIBE {gpdb.table.alias_or_name}",
            ).df().to_dict("records")
        ]

    assert set(cols) == {
            "symbol_name",
            "gene_set_rank",
            "gene_sets_test_gene_set_1",
            "gene_sets_test_gene_set_2",
            "gene_sets_test_gene_set_3",
            "gene_score_gene_score1",
            "t4c8_dataset_autism_denovo_lgds",
            "t4c8_dataset_autism_denovo_lgds_rate",
            "t4c8_dataset_autism_denovo_missense",
            "t4c8_dataset_autism_denovo_missense_rate",
            "t4c8_dataset_autism_rare_lgds",
            "t4c8_dataset_autism_rare_lgds_rate",
            "t4c8_dataset_autism_rare_missense",
            "t4c8_dataset_autism_rare_missense_rate",
            "t4c8_dataset_autism_rare_score_one_06",
            "t4c8_dataset_autism_rare_score_one_06_rate",
            "t4c8_dataset_epilepsy_denovo_lgds",
            "t4c8_dataset_epilepsy_denovo_lgds_rate",
            "t4c8_dataset_epilepsy_denovo_missense",
            "t4c8_dataset_epilepsy_denovo_missense_rate",
            "t4c8_dataset_epilepsy_rare_lgds",
            "t4c8_dataset_epilepsy_rare_lgds_rate",
            "t4c8_dataset_epilepsy_rare_missense",
            "t4c8_dataset_epilepsy_rare_missense_rate",
            "t4c8_dataset_epilepsy_rare_score_one_06",
            "t4c8_dataset_epilepsy_rare_score_one_06_rate",
            "t4c8_dataset_unaffected_denovo_lgds",
            "t4c8_dataset_unaffected_denovo_lgds_rate",
            "t4c8_dataset_unaffected_denovo_missense",
            "t4c8_dataset_unaffected_denovo_missense_rate",
            "t4c8_dataset_unaffected_rare_lgds",
            "t4c8_dataset_unaffected_rare_lgds_rate",
            "t4c8_dataset_unaffected_rare_missense",
            "t4c8_dataset_unaffected_rare_missense_rate",
            "t4c8_dataset_unaffected_rare_score_one_06",
            "t4c8_dataset_unaffected_rare_score_one_06_rate",
            "t4c8_study_3_autism_denovo_lgds",
            "t4c8_study_3_autism_denovo_lgds_rate",
            "t4c8_study_3_autism_denovo_missense",
            "t4c8_study_3_autism_denovo_missense_rate",
            "t4c8_study_3_autism_rare_lgds",
            "t4c8_study_3_autism_rare_lgds_rate",
            "t4c8_study_3_autism_rare_missense",
            "t4c8_study_3_autism_rare_missense_rate",
            "t4c8_study_3_autism_rare_score_one_06",
            "t4c8_study_3_autism_rare_score_one_06_rate",
            "t4c8_study_3_unaffected_denovo_lgds",
            "t4c8_study_3_unaffected_denovo_lgds_rate",
            "t4c8_study_3_unaffected_denovo_missense",
            "t4c8_study_3_unaffected_denovo_missense_rate",
            "t4c8_study_3_unaffected_rare_lgds",
            "t4c8_study_3_unaffected_rare_lgds_rate",
            "t4c8_study_3_unaffected_rare_missense",
            "t4c8_study_3_unaffected_rare_missense_rate",
            "t4c8_study_3_unaffected_rare_score_one_06",
            "t4c8_study_3_unaffected_rare_score_one_06_rate",
        }


def test_collect_denovo_variant_counts(
    gp_t4c8_instance: GPFInstance,
    mocker: pytest_mock.MockFixture,
) -> None:
    assert gp_t4c8_instance is not None
    mocker.patch(
        "dae.gene_profile.generate_gene_profile."
        "RARE_FREQUENCY_THRESHOLD", return_value=50.0)

    # pylint: disable=protected-access, invalid-name
    gp_config = gp_t4c8_instance._gene_profile_config
    assert gp_config is not None
    dataset = gp_t4c8_instance.get_dataset("t4c8_dataset")
    assert dataset is not None
    gene_symbols = {"t4", "c8"}

    denovo_variants = list(
        dataset.query_variants(
            regions=None,
            genes=["t4", "c8"],
            inheritance="denovo",
            unique_family_variants=True,
        ))
    person_ids = _collect_person_set_collections(
        gp_t4c8_instance, gp_config)

    variant_counts = _init_variant_counts(
        gp_config, gene_symbols)

    collect_variant_counts(
        variant_counts["t4c8_dataset"],
        denovo_variants,
        "t4c8_dataset",
        gp_config,
        person_ids["t4c8_dataset"],
        denovo_flag=True,
    )
    collect_variant_counts(
        variant_counts["t4c8_dataset"],
        denovo_variants,
        "t4c8_dataset",
        gp_config,
        person_ids["t4c8_dataset"],
        denovo_flag=True,
    )

    assert variant_counts["t4c8_dataset"]["c8"]["autism"] == {
        "denovo_lgds": {"f1.3.chr1:122.A.C,AC"},
        "denovo_missense": {"f1.1.chr1:119.A.C"},
        "rare_lgds": set(),
        "rare_missense": set(),
        "rare_score_one_06": set(),
    }


def test_collect_rare_variant_counts(
    gp_t4c8_instance: GPFInstance,
    mocker: pytest_mock.MockFixture,
) -> None:
    assert gp_t4c8_instance is not None
    mocker.patch(
        "dae.gene_profile.generate_gene_profile."
        "RARE_FREQUENCY_THRESHOLD", 100.0)

    # pylint: disable=protected-access, invalid-name
    gp_config = gp_t4c8_instance._gene_profile_config
    assert gp_config is not None
    dataset = gp_t4c8_instance.get_dataset("t4c8_dataset")
    assert dataset is not None
    gene_symbols = {"t4", "c8"}
    person_ids = _collect_person_set_collections(
        gp_t4c8_instance, gp_config)

    statistics = gp_config.datasets["t4c8_dataset"].statistics
    query_kwargs = merge_rare_queries(statistics)

    rare_variants = list(
        dataset.query_variants(
            regions=None,
            genes=["t4", "c8"],
            **query_kwargs,
        ))

    variant_counts = _init_variant_counts(
        gp_config, gene_symbols)

    collect_variant_counts(
        variant_counts["t4c8_dataset"],
        rare_variants,
        "t4c8_dataset",
        gp_config,
        person_ids["t4c8_dataset"],
        denovo_flag=False,
    )
    collect_variant_counts(
        variant_counts["t4c8_dataset"],
        rare_variants,
        "t4c8_dataset",
        gp_config,
        person_ids["t4c8_dataset"],
        denovo_flag=False,
    )

    assert variant_counts["t4c8_dataset"]["c8"]["autism"] == {
        "denovo_lgds": set(),
        "denovo_missense": set(),
        "rare_lgds": {"f1.3.chr1:122.A.C,AC"},
        "rare_missense": {"f1.3.chr1:119.A.G,C"},
        "rare_score_one_06": {
            "f1.3.chr1:122.A.C,AC",
        },
    }


def test_calculate_variant_counts(
    gp_t4c8_instance: GPFInstance,
    mocker: pytest_mock.MockFixture,
) -> None:
    assert gp_t4c8_instance is not None
    mocker.patch(
        "dae.gene_profile.generate_gene_profile."
        "RARE_FREQUENCY_THRESHOLD", 100.0)

    # pylint: disable=protected-access, invalid-name
    gp_config = gp_t4c8_instance._gene_profile_config
    assert gp_config is not None
    dataset = gp_t4c8_instance.get_dataset("t4c8_dataset")
    assert dataset is not None
    gene_symbols = {"t4", "c8"}
    person_ids = _collect_person_set_collections(
        gp_t4c8_instance, gp_config)

    variant_counts = _calculate_variant_counts(
        gp_t4c8_instance,
        gp_config,
        gene_symbols,
        person_ids,
        [None],
        jobs=1,
    )

    assert variant_counts["t4c8_dataset"]["c8"]["autism"] == {
        "denovo_lgds": {"f1.3.chr1:122.A.C,AC"},
        "denovo_missense": {"f1.1.chr1:119.A.C"},
        "rare_lgds": {"f1.3.chr1:122.A.C,AC"},
        "rare_missense": {"f1.3.chr1:119.A.G,C"},
        "rare_score_one_06": {
            "f1.3.chr1:122.A.C,AC",
        },
    }
    assert variant_counts["t4c8_dataset"]["c8"]["unaffected"] == {
        "denovo_lgds": {"f1.3.chr1:122.A.C,AC"},
        "denovo_missense": {"f1.1.chr1:119.A.C"},
        "rare_lgds": {"f1.3.chr1:122.A.C,AC"},
        "rare_missense": {"f1.3.chr1:119.A.G,C"},
        "rare_score_one_06": {
            "f1.3.chr1:122.A.C,AC",
        },
    }

    assert variant_counts["t4c8_study_3"]["c8"]["autism"] == {
        "denovo_lgds": set(),
        "denovo_missense": set(),
        "rare_lgds": set(),
        "rare_missense": {"f3.1.chr1:117.T.G"},
        "rare_score_one_06": set(),
    }


@pytest.mark.parametrize(
    "chromsomes,gm_chromosomes,kwargs,expected_partitions", [
        ({"chr1", "chr2", "chrY"},
         {"chr1", "chr2", "chrY"},
         {},
         [[Region("chr1")], [Region("chr2")], [Region("chrY")]]),
        ({"chr1", "chr2", "chrY"},
         {"chr1", "chr2", "chrY"},
         {"split_by_chromosome": False},
         [None]),
        ({"chr1", "chrY", "GL1", "GL2"},
         {"chr1", "chrY", "GL1"},
         {},
         [[Region("chr1")], [Region("GL1"), Region("chrY")]]),
    ],
)
def test_build_partitions(
    mocker: pytest_mock.MockFixture,
    chromsomes: set,
    gm_chromosomes: set,
    kwargs: dict,
    expected_partitions: list[list[Region] | None],
) -> None:

    reference_genome = mocker.Mock()
    gene_models = mocker.Mock()
    reference_genome.chromosomes = chromsomes
    gene_models.has_chromosome = lambda chrom: chrom in gm_chromosomes

    partitions = build_partitions(
        reference_genome,
        gene_models,
        **kwargs,
    )
    assert partitions == expected_partitions


def test_merge_variant_counts(
    gp_config: Box,
) -> None:
    gene_symbols = {"t4", "c8"}
    variant_counts1 = {
        "t4c8_dataset": {
            "t4": {
                "autism": {
                    "denovo_lgds": {"v1", "v2"},
                    "denovo_missense": {"v3"},
                    "rare_lgds": set(),
                    "rare_missense": set(),
                },
            },
            "c8": {
                "autism": {
                    "denovo_lgds": {"v7"},
                    "denovo_missense": {"v8"},
                    "rare_lgds": set(),
                    "rare_missense": set(),
                },
            },
        },
        "t4c8_study_3": {
            "t4": {
                "autism": {
                    "denovo_lgds": {"v4"},
                    "denovo_missense": {"v5"},
                    "rare_lgds": set(),
                    "rare_missense": {"v6"},
                },
            },
        },
    }
    variant_counts2 = {
        "t4c8_dataset": {
            "t4": {
                "autism": {
                    "denovo_lgds": {"v2", "v4"},
                    "denovo_missense": {"v3", "v5"},
                    "rare_lgds": {"v6"},
                    "rare_missense": set(),
                },
            },
        },
        "t4c8_study_3": {
            "t4": {
                "autism": {
                    "denovo_lgds": {"v4", "v7"},
                    "denovo_missense": {"v5", "v8"},
                    "rare_lgds": set(),
                    "rare_missense": {"v6", "v9"},
                },
            },
        },
    }

    merged_counts = _merge_variant_counts(
            gp_config, gene_symbols, variant_counts1, variant_counts2)

    assert merged_counts == {
        "t4c8_dataset": {
            "t4": {
                "autism": {
                    "denovo_lgds": {"v1", "v2", "v4"},
                    "denovo_missense": {"v3", "v5"},
                    "rare_lgds": {"v6"},
                    "rare_missense": set(),
                    "rare_score_one_06": set(),
                },
                "epilepsy": {
                    "denovo_lgds": set(),
                    "denovo_missense": set(),
                    "rare_lgds": set(),
                    "rare_missense": set(),
                    "rare_score_one_06": set(),
                },
                "unaffected": {
                    "denovo_lgds": set(),
                    "denovo_missense": set(),
                    "rare_lgds": set(),
                    "rare_missense": set(),
                    "rare_score_one_06": set(),
                },
            },
            "c8": {
                "autism": {
                    "denovo_lgds": {"v7"},
                    "denovo_missense": {"v8"},
                    "rare_lgds": set(),
                    "rare_missense": set(),
                    "rare_score_one_06": set(),
                },
                "epilepsy": {
                    "denovo_lgds": set(),
                    "denovo_missense": set(),
                    "rare_lgds": set(),
                    "rare_missense": set(),
                    "rare_score_one_06": set(),
                },
                "unaffected": {
                    "denovo_lgds": set(),
                    "denovo_missense": set(),
                    "rare_lgds": set(),
                    "rare_missense": set(),
                    "rare_score_one_06": set(),
                },
            },
        },
        "t4c8_study_3": {
            "t4": {
                "autism": {
                    "denovo_lgds": {"v4", "v7"},
                    "denovo_missense": {"v5", "v8"},
                    "rare_lgds": set(),
                    "rare_missense": {"v6", "v9"},
                    "rare_score_one_06": set(),
                },
                "unaffected": {
                    "denovo_lgds": set(),
                    "denovo_missense": set(),
                    "rare_lgds": set(),
                    "rare_missense": set(),
                    "rare_score_one_06": set(),
                },
            },
            "c8": {
                "autism": {
                    "denovo_lgds": set(),
                    "denovo_missense": set(),
                    "rare_lgds": set(),
                    "rare_missense": set(),
                    "rare_score_one_06": set(),
                },
                "unaffected": {
                    "denovo_lgds": set(),
                    "denovo_missense": set(),
                    "rare_lgds": set(),
                    "rare_missense": set(),
                    "rare_score_one_06": set(),
                },
            },
        },
    }
