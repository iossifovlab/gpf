# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from gpf_instance.gpf_instance import WGPFInstance


def test_scores_created(
    t4c8_wgpf_instance: WGPFInstance,  # setup WGPF instance
) -> None:
    assert t4c8_wgpf_instance.gene_scores_db is not None


def test_t4c8_score_available(
    t4c8_wgpf_instance: WGPFInstance,  # setup WGPF instance
) -> None:
    assert "t4c8_score" in t4c8_wgpf_instance.gene_scores_db


def test_get_t4c8_score(
    t4c8_wgpf_instance: WGPFInstance,  # setup WGPF instance
) -> None:
    score = t4c8_wgpf_instance.gene_scores_db.get_gene_score(
        "gene_scores/t4c8_score")

    assert score is not None
    assert score.get_min("t4c8_score") == pytest.approx(10.123456789)
    assert score.get_max("t4c8_score") == pytest.approx(20.0)


def test_get_genes_by_score(
    t4c8_wgpf_instance: WGPFInstance,  # setup WGPF instance
) -> None:
    gene_score = t4c8_wgpf_instance.gene_scores_db.get_gene_score(
        "gene_scores/t4c8_score")
    assert gene_score is not None

    genes = gene_score.get_genes(
        "t4c8_score", 1.0, 4.0,
    )
    assert len(genes) == 0

    genes = gene_score.get_genes(
        "t4c8_score", 5.0, 15.0,
    )
    assert len(genes) == 1

    genes = gene_score.get_genes(
        "t4c8_score", 0, 205,
    )
    assert len(genes) == 2
