from __future__ import unicode_literals
import pytest

pytestmark = pytest.mark.usefixtures(
    'gene_info_cache_dir', 'calc_gene_sets', 'cleanup_gene_sets')


def test_denovo_gene_sets_exist(denovo_gene_sets_facade):
    denovo = denovo_gene_sets_facade.has_denovo_gene_set('denovo')
    assert denovo


def test_get_all_gene_sets(denovo_gene_sets_facade):
    gene_sets_collections = \
        denovo_gene_sets_facade.get_collections_descriptions()
    assert len(gene_sets_collections) != 0
