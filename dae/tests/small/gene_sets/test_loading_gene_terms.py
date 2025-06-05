# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
from collections.abc import Callable

import pytest

from dae.gene_sets.gene_term import (
    load_gene_terms,
    load_ncbi_gene_info,
    rename_gene_terms,
)


@pytest.fixture()
def fixture_filename() -> Callable:
    def _fixture_filename(filename: str) -> str:
        return os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "fixtures",
            filename)

    return _fixture_filename


def test_load_ncbi_gene_info(fixture_filename: Callable[[str], str]) -> None:
    gene_info_file = fixture_filename("reduced-humanGeneInfo.txt")
    result = load_ncbi_gene_info(gene_info_file)

    assert result is not None


def test_load_protein_domains(fixture_filename: Callable[[str], str]) -> None:
    domains_filename = fixture_filename("reduced-Domain-map.txt")
    domains = load_gene_terms(domains_filename)
    assert domains is not None

    gene_info_file = fixture_filename("reduced-humanGeneInfo.txt")
    ncbi_gene_info = load_ncbi_gene_info(gene_info_file)

    result = rename_gene_terms(domains, "sym", ncbi_gene_info)

    assert result is not None
    assert len(result.t2g["CRF"]) == 2
    assert set(result.t2g["CRF"].keys()) == {"NOS1AP", "UCN2"}
    assert len(result.t2g["TAFH"]) == 5
    assert set(result.t2g["TAFH"].keys()) == {
        "CBFA2T3",
        "TAF4B",
        "TAF4",
        "RUNX1T1",
        "CBFA2T2",
    }


def test_load_gmt_file(fixture_filename: Callable[[str], str]) -> None:
    gene_terms = load_gene_terms(
        fixture_filename("reduced-c2.all.v4.0.symbols.gmt"))
    assert gene_terms is not None

    assert len(gene_terms.t2g[
        "KEGG_PENTOSE_AND_GLUCURONATE_INTERCONVERSIONS"]) == 28

    assert set(gene_terms.t2g[
        "KEGG_PENTOSE_AND_GLUCURONATE_INTERCONVERSIONS"].keys()) == {
            "AKR1B1",
            "UGT2B7",
            "UGT1A10",
            "UGT1A6",
            "GUSB",
            "UGT2A3",
            "DHDH",
            "UGT2B28",
            "UGT1A4",
            "LOC729020",
            "RPE",
            "CRYL1",
            "UGT1A3",
            "UGT2A1",
            "UGT2B10",
            "UGT2B4",
            "UGDH",
            "UGT1A7",
            "UGT2B11",
            "XYLB",
            "UGT1A1",
            "UGT2B15",
            "UGP2",
            "UGT1A8",
            "UGT2B17",
            "UGT1A5",
            "DCXR",
          "UGT1A9",
        }


def test_load_gene_sets_directory(
    fixture_filename: Callable[[str], str],
) -> None:

    gene_terms = load_gene_terms(
        fixture_filename("GeneSets"))
    assert gene_terms is not None

    assert len(gene_terms.t2g["Main Candidates"]) == 9
    assert set(gene_terms.t2g["Main Candidates"].keys()) == {
        "POGZ",
        "CHD8",
        "ANK2",
        "FAT4",
        "NBEA",
        "CELSR1",
        "USP7",
        "GOLGA5",
        "PCSK2",
    }
    assert gene_terms.t_desc["Main Candidates"] == \
        "Description of gene set Main Candidates"
