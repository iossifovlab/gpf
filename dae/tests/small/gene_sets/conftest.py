# pylint: disable=W0621,C0114,C0116,W0212,W0613

import os
import textwrap
from typing import Any, cast

import pytest
from dae.gene_sets.denovo_gene_set_collection import DenovoGeneSetCollection
from dae.gene_sets.denovo_gene_set_helpers import (
    DenovoGeneSetHelpers,
)
from dae.gene_sets.denovo_gene_sets_db import DenovoGeneSetsDb
from dae.gene_sets.gene_sets_db import GeneSetCollection, GeneSetsDb
from dae.genomic_resources.repository import (
    GR_CONF_FILE_NAME,
    GenomicResourceRepo,
)
from dae.genomic_resources.testing import (
    build_inmemory_test_repository,
    convert_to_tab_separated,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData
from dae.testing import denovo_study, setup_denovo, setup_pedigree
from dae.testing.foobar_import import foobar_gpf
from dae.utils.fixtures import path_to_fixtures as _path_to_fixtures


def fixtures_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures"))


def path_to_fixtures(*args: Any) -> str:
    return cast(str, _path_to_fixtures("gene", *args))


@pytest.fixture(scope="session")
def t4c8_denovo_gene_sets(
    t4c8_instance: GPFInstance,
) -> list[DenovoGeneSetCollection]:
    result = [
        DenovoGeneSetHelpers.load_collection(
            t4c8_instance.get_genotype_data("t4c8_study_1"),
        ),
        DenovoGeneSetHelpers.load_collection(
            t4c8_instance.get_genotype_data("t4c8_study_2"),
        ),
        DenovoGeneSetHelpers.load_collection(
            t4c8_instance.get_genotype_data("t4c8_study_4"),
        ),
    ]
    return list(filter(None, result))


@pytest.fixture(scope="session")
def trios2_study(
    tmp_path_factory: pytest.TempPathFactory,
) -> GenotypeData:
    root_path = tmp_path_factory.mktemp(
        "denovo_gene_sets_tios")
    gpf_instance = foobar_gpf(root_path)
    ped_path = setup_pedigree(
        root_path / "trios2_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        f1       s1       d1     m1     2   1      sib
        f2       m2       0      0      2   1      mom
        f2       d2       0      0      1   1      dad
        f2       p2       d2     m2     2   2      prb
        """)
    vcf_path = setup_denovo(
        root_path / "trios2_data" / "in.tsv",
        """
          chrom  pos  ref  alt   person_id
          foo    7    A    G     p1
          foo    14   C    T     s1
          bar    7    C    CCCCC p2
          bar    7    C    A     p2
          bar    7    C    T     p1
        """,
    )

    return denovo_study(
        root_path,
        "trios2", ped_path, [vcf_path],
        gpf_instance,
        study_config_update={
            "id": "trios2",
            "denovo_gene_sets": {
                "enabled": True,
            },
        })


@pytest.fixture(scope="session")
def trios2_dgsc(
    trios2_study: GenotypeData,
) -> DenovoGeneSetCollection:
    DenovoGeneSetHelpers.build_collection(trios2_study)
    result = DenovoGeneSetHelpers.load_collection(trios2_study)
    assert result is not None
    return result


@pytest.fixture(scope="session")
def t4c8_denovo_gene_sets_db(
    t4c8_instance: GPFInstance,
) -> DenovoGeneSetsDb:
    return t4c8_instance.denovo_gene_sets_db


@pytest.fixture
def grr_contents() -> dict[str, Any]:
    return {
        "main": {
            GR_CONF_FILE_NAME: textwrap.dedent("""
                type: gene_set
                id: main
                format: directory
                directory: GeneSets
                web_label: Main
                web_format_str: "key| (|count|): |desc"
                """),
            "GeneSets": {
                "main_candidates.txt": (
                    "main_candidates\n"
                    "Main Candidates\n"
                    "POGZ\n"
                    "CHD8\n"
                    "ANK2\n"
                    "FAT4\n"
                    "NBEA\n"
                    "CELSR1\n"
                    "USP7\n"
                    "GOLGA5\n"
                    "PCSK2\n"
                ),
                "alt_candidates.txt": (
                    "alt_candidates\n"
                    "Alt Candidates\n"
                    "DIABLO\n"
                ),
            },
        },
        "test_mapping": {
            GR_CONF_FILE_NAME: textwrap.dedent("""
                type: gene_set
                id: test_mapping
                format: map
                filename: test-map.txt
                web_label: Test mapping
                web_format_str: "key| (|count|)"
            """),
            "test-map.txt": (
                "#geneNS\tsym\n"
                "POGZ\ttest:01 test:02\n"
                "CHD8\ttest:02 test:03\n"
            ),
            "test-mapnames.txt": (
                "test:01\ttest_first\n"
                "test:02\ttest_second\n"
                "test:03\ttest_third\n"
            ),
        },
        "test_gmt": {
            GR_CONF_FILE_NAME: textwrap.dedent("""
                type: gene_set
                id: test_gmt
                format: gmt
                filename: test-gmt.gmt
                web_label: Test GMT
                web_format_str: "key| (|count|)"
            """),
            "test-gmt.gmt": (
                "TEST_GENE_SET1\tsomedescription\tPOGZ\tCHD8\n"
                "TEST_GENE_SET2\tsomedescription\tANK2\tFAT4\n"
                "TEST_GENE_SET3\tsomedescription\tPOGZ\n"
            ),
        },
        "test": {
            GR_CONF_FILE_NAME: textwrap.dedent("""
                type: gene_set
                id: test_mapping
                format: map
                filename: test-map.txt
                web_label: Test mapping
                web_format_str: "key| (|count|)"
            """),
            "test-map.txt": convert_to_tab_separated("""
                #geneNS tsym
                POGZ    test:01||test:02
                CHD8    test:02||test:03
            """),
            "test-mapnames.txt": convert_to_tab_separated("""
                test:01  test_first
                test:02  test_second
                test:03  test_third
            """),
        },
    }


@pytest.fixture
def gene_sets_repo_in_memory(grr_contents) -> GenomicResourceRepo:
    return build_inmemory_test_repository(grr_contents)


@pytest.fixture
def gene_sets_db(
    gene_sets_repo_in_memory: GenomicResourceRepo,
) -> GeneSetsDb:
    resources = [
        gene_sets_repo_in_memory.get_resource("main"),
        gene_sets_repo_in_memory.get_resource("test_mapping"),
        gene_sets_repo_in_memory.get_resource("test_gmt"),
    ]
    gene_set_collections = [
        GeneSetCollection(r) for r in resources
    ]
    return GeneSetsDb(gene_set_collections)
