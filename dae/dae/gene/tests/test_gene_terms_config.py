from dae.gene.tests.conftest import fixtures_dir


def test_gene_terms_config(gene_info_config):
    assert gene_info_config.gene_terms

    gene_terms = gene_info_config.gene_terms

    assert len(gene_terms.keys()) == 2
    assert sorted(gene_terms.keys()) == sorted(['main', 'term_curated'])

    assert gene_terms.main.file == f'{fixtures_dir()}/geneInfo/GeneSets'
    assert gene_terms.main.webFormatStr == 'key| (|count|): |desc'
    assert gene_terms.main.webLabel == 'Main'
