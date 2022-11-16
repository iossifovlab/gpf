# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.testing import setup_gpf_instance, setup_genome, \
    setup_empty_gene_models


@pytest.fixture
def alla_instance(tmp_path_factory):
    # Given
    root_path = tmp_path_factory.mktemp("internal_storage_test")

    genome = setup_genome(
        root_path / "alla_gpf" / "genome" / "allChr.fa",
        f"""
        >chrA
        {100 * "A"}
        """
    )
    empty_gene_models = setup_empty_gene_models(
        root_path / "alla_gpf" / "empty_gene_models" / "empty_genes.txt")
    return setup_gpf_instance(
        root_path / "gpf_instance",
        reference_genome=genome,
        gene_models=empty_gene_models,
    )


def test_empty_gene_scores(alla_instance):
    assert len(alla_instance.gene_scores_db) == 0


def test_has_gene_score(alla_instance):
    assert not alla_instance.has_gene_score("ala-bala")


def test_get_gene_score(alla_instance):
    assert alla_instance.get_gene_score("ala-bala") is None


def test_get_all_gene_scores(alla_instance):
    assert len(alla_instance.get_all_gene_scores()) == 0


def test_empty_genomic_scores(alla_instance):
    assert len(alla_instance.genomic_scores_db) == 0


def test_empty_gene_sets(alla_instance):
    assert len(alla_instance.gene_sets_db) == 0


def test_empty_denovo_gene_sets(alla_instance):
    assert len(alla_instance.denovo_gene_sets_db) == 0


def test_empty_genotype_data(alla_instance):
    assert len(alla_instance.get_genotype_data_ids()) == 0


def test_empty_phenotype_data(alla_instance):
    assert len(alla_instance.get_phenotype_data_ids()) == 0
