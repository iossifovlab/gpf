import pytest

pytestmark = pytest.mark.usefixtures("mock_studies_manager")


def test_weights_created(weights_loader):
    assert weights_loader is not None


def test_lgd_rank_available(weights_loader):
    assert 'LGD_rank' in weights_loader


def test_get_lgd_rank(weights_loader):
    w = weights_loader['LGD_rank']

    assert w is not None
    assert w.min() == pytest.approx(1.0, 0.01)
    assert w.max() == pytest.approx(18394.5, 0.01)


def test_get_genes_by_weight(weights_loader):
    g = weights_loader['LGD_rank'].get_genes(1.5, 5.0)
    assert len(g) == 3

    g = weights_loader['LGD_rank'].get_genes(-1, 5.0)
    assert len(g) == 4

    g = weights_loader['LGD_rank'].get_genes(1.0, 5.0)
    assert len(g) == 4
