# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import re
import textwrap
import pytest
import yaml

from dae.testing.import_helpers import vcf_study
from dae.genomic_resources.testing import \
    setup_directories, setup_pedigree, setup_vcf
from dae.testing.t4c8_import import t4c8_gpf
from dae.gene_profile.generate_gene_profile import main
from dae.gene_profile.db import GeneProfileDB
from dae.gpf_instance.gpf_instance import GPFInstance


@pytest.fixture
def gp_config() -> dict:
    return {
        "gene_links": [
            {
                "name": "Link with prefix",
                "url": "{gpf_prefix}/datasets/{gene}"
            },
            {
                "name": "Link with gene info",
                "url": (
                    "https://site.com/{gene}?db={genome}&"
                    "position={chromosome_prefix}{chromosome}"
                    "/{gene_start_position}-{gene_stop_position}"
                )
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
                        "collection_id": "gene_sets"
                    },
                    {
                        "set_id": "test_gene_set_2",
                        "collection_id": "gene_sets"
                    },
                    {
                        "set_id": "test_gene_set_3",
                        "collection_id": "gene_sets"
                    },
                ]
            },
        ],
        "genomic_scores": [
            {
                "category": "gene_score",
                "display_name": "Test gene score",
                "scores": [
                    {"score_name": "gene_score1", "format": "%%s"},
                ]
            }
        ],
        "datasets": {
            "study_1": {
                "statistics": [
                    {
                        "id": "lgds",
                        "display_name": "LGDs",
                        "effects": ["LGDs"],
                        "category": "denovo"
                    },
                    {
                        "id": "denovo_missense",
                        "display_name": "missense",
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
            }
        }
    }


def gp_gpf_instance(
        gp_config: str,
        tmp_path: pathlib.Path) -> GPFInstance:
    setup_directories(
        tmp_path,
        {
            "gpf_instance": {
                "gp_config.yaml": yaml.dump(
                    gp_config, default_flow_style=False),
                "gpf_instance.yaml": textwrap.dedent("""
                    instance_id: test_instance
                    gene_profiles_config:
                        conf_file: "gp_config.yaml"
                    gene_sets_db:
                        gene_set_collections:
                        - gene_sets
                    gene_scores_db:
                        gene_scores:
                        - gene_score1
                """),
            },
            "gene_sets": {
                "genomic_resource.yaml": textwrap.dedent("""
                    type: gene_set
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
                }
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
        }
    )

    ped_path = setup_pedigree(
        tmp_path / "study_1" / "pedigree" / "in.ped",
        """
familyId personId dadId momId sex status role
f1.1     mom1     0     0     2   1      mom
f1.1     dad1     0     0     1   1      dad
f1.1     ch1      dad1  mom1  2   2      prb
f1.3     mom3     0     0     2   1      mom
f1.3     dad3     0     0     1   1      dad
f1.3     ch3      dad3  mom3  2   1      prb
        """)
    vcf_path = setup_vcf(
        tmp_path / "study_1" / "vcf" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
##contig=<ID=chr3>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 ch1 mom3 dad3 ch3
chr1   15  .  AG  A   .    .      .    GT     0/0  0/0  0/1 0/0  0/0  0/0
chr1   15  .  A   C   .    .      .    GT     0/0  0/0  0/0 0/0  0/0  0/1
chr1   35  .  G   A   .    .      .    GT     0/0  0/0  0/1 0/0  0/0  0/0
chr1   35  .  G   C   .    .      .    GT     0/0  0/0  0/0 0/0  0/0  0/1
chr1   126 .  T   A   .    .      .    GT     0/0  0/0  0/1 0/0  0/0  0/0
chr1   135 .  T   A   .    .      .    GT     0/0  0/0  0/0 0/0  0/0  0/1
chr1   165 .  G   T   .    .      .    GT     0/0  0/1  0/1 0/0  0/0  0/0
chr1   195 .  C   T   .    .      .    GT     0/0  0/0  0/1 0/0  0/0  0/0
        """)  # noqa

    project_config_update = {
        "input": {
            "vcf": {
                "denovo_mode": "denovo",
                "omission_mode": "omission",
            }
        },
    }

    instance = t4c8_gpf(tmp_path)

    vcf_study(
        tmp_path,
        "study_1", ped_path, [vcf_path],
        instance,
        project_config_update=project_config_update,
        study_config_update={
            "conf_dir": str(tmp_path / "study_1"),
            "person_set_collections": {
                "phenotype": {
                    "id": "phenotype",
                    "name": "Phenotype",
                    "sources": [
                        {
                            "from": "pedigree",
                            "source": "status"
                        }
                    ],
                    "default": {
                        "color": "#aaaaaa",
                        "id": "unspecified",
                        "name": "unspecified",
                    },
                    "domain": [
                        {
                            "color": "#bbbbbb",
                            "id": "autism",
                            "name": "autism",
                            "values": [
                                "affected"
                            ]
                        },
                        {
                            "color": "#00ff00",
                            "id": "unaffected",
                            "name": "unaffected",
                            "values": [
                                "unaffected"
                            ]
                        },
                    ]
                },
                "selected_person_set_collections": [
                    "phenotype"
                ]
            }
        })

    return instance


def test_generate_gene_profile(
        gp_config: dict,
        tmp_path: pathlib.Path) -> None:
    gpdb_filename = str(tmp_path / "gpdb")
    argv = [
        "--dbfile",
        gpdb_filename,
        "-vv",
    ]

    gpf_instance = gp_gpf_instance(gp_config, tmp_path)
    main(gpf_instance, argv)
    gpdb = GeneProfileDB(
        gpf_instance._gene_profile_config,
        gpdb_filename,
        clear=False
    )

    t4 = gpdb.get_gp("t4")
    c8 = gpdb.get_gp("c8")

    assert t4.gene_sets == [
        "gene_sets_test_gene_set_1",
        "gene_sets_test_gene_set_3"
    ]
    assert c8.gene_sets == [
        "gene_sets_test_gene_set_2",
        "gene_sets_test_gene_set_3"
    ]

    assert t4.genomic_scores == {
        "gene_score": {
            "gene_score1": {
                "format": "%s",
                "value": 10.0
            }
        }
    }

    assert c8.genomic_scores == {
        "gene_score": {
            "gene_score1": {
                "format": "%s",
                "value": 20.0
            }
        }
    }

    assert t4.variant_counts == {
        "study_1": {
            "autism": {
                "lgds": {
                    "count": 1.0,
                    "rate": 1000.0
                },
                "denovo_missense": {
                    "count": 1.0,
                    "rate": 1000.0
                }
            },
            "unaffected": {
                "lgds": {
                    "count": 0.0,
                    "rate": 0.0
                },
                "denovo_missense": {
                    "count": 2.0,
                    "rate": 2000.0
                }
            }
        }
    }

    assert c8.variant_counts == {
        "study_1": {
            "autism": {
                "lgds": {
                    "count": 1.0,
                    "rate": 1000.0
                },
                "denovo_missense": {
                    "count": 1.0,
                    "rate": 1000.0
                }
            },
            "unaffected": {
                "lgds": {
                    "count": 1.0,
                    "rate": 1000.0
                },
                "denovo_missense": {
                    "count": 0.0,
                    "rate": 0.0
                }
            }
        }
    }


def test_generate_gene_profile_with_incomplete_config(
        gp_config: str,
        tmp_path: pathlib.Path) -> None:
    gpdb_filename = str(tmp_path / "gpdb")
    argv = [
        "--dbfile",
        gpdb_filename,
        "-vv",
    ]
    del gp_config["order"]
    del gp_config["default_dataset"]

    gpf_instance = gp_gpf_instance(gp_config, tmp_path)
    expected_error = re.escape(
        "/gpf_instance: {'default_dataset': "
        + "['required field'], 'order': ['required field']}")
    with pytest.raises(
            ValueError,
            match=r"^(.*?)" + expected_error):
        main(gpf_instance, argv)


def test_generate_gene_profile_with_incomplete_config_order(
        gp_config: str,
        tmp_path: pathlib.Path) -> None:
    gpdb_filename = str(tmp_path / "gpdb")
    argv = [
        "--dbfile",
        gpdb_filename,
        "-vv",
    ]

    gp_config["order"] = [
        "gene_set_rank",
        "gene_scr",
        "study_1",
    ]
    gpf_instance = gp_gpf_instance(gp_config, tmp_path)

    with pytest.raises(
            AssertionError,
            match="Given GP order has invalid entries"):
        main(gpf_instance, argv)
