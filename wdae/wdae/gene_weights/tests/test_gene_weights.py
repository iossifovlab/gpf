import pytest

pytestmark = pytest.mark.usefixtures('mock_gpf_instance')


def test_weights_created(weights_factory):
    assert weights_factory is not None


def test_lgd_rank_available(weights_factory):
    assert 'LGD_rank' in weights_factory


def test_get_lgd_rank(weights_factory):
    w = weights_factory['LGD_rank']

    assert w is not None
    assert w.min() == pytest.approx(1.0, 0.01)
    assert w.max() == pytest.approx(18394.5, 0.01)


def test_get_genes_by_weight(weights_factory):
    g = weights_factory['LGD_rank'].get_genes(1.5, 5.0)
    assert len(g) == 3

    g = weights_factory['LGD_rank'].get_genes(-1, 5.0)
    assert len(g) == 4

    g = weights_factory['LGD_rank'].get_genes(1.0, 5.0)
    assert len(g) == 4
