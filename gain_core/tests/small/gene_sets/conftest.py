# pylint: disable=W0621,C0114,C0116,W0212,W0613

import os
import textwrap
from typing import Any

import pytest
from gain.genomic_resources.repository import (
    GR_CONF_FILE_NAME,
    GenomicResourceRepo,
)
from gain.genomic_resources.testing import (
    build_inmemory_test_repository,
    convert_to_tab_separated,
)


def fixtures_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures"))


@pytest.fixture
def grr_contents() -> dict[str, Any]:
    return {
        "main": {
            GR_CONF_FILE_NAME: textwrap.dedent("""
                type: gene_set_collection
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
                type: gene_set_collection
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
                type: gene_set_collection
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
                type: gene_set_collection
                id: test_mapping
                format: map
                filename: test-map.txt
                web_label: Test mapping
                web_format_str: "key| (|count|)"
                histograms:
                  genes_per_gene_set:
                    type: categorical
                    natural_order: True
                  gene_sets_per_gene:
                    type: categorical
                    natural_order: True
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
def gene_sets_repo_in_memory(
    grr_contents: dict[str, Any],
) -> GenomicResourceRepo:
    return build_inmemory_test_repository(grr_contents)
