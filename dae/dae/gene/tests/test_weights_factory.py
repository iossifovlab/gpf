def test_weights_default(weights_factory):
    assert weights_factory is not None


def test_weights_rvis_rank(weights_factory):
    assert weights_factory['RVIS_rank'] is not None

    rvis = weights_factory['RVIS_rank']
    assert rvis.df is not None

    assert 'RVIS_rank' in rvis.df.columns


def test_weights_has_rvis_rank(weights_factory):
    assert 'RVIS_rank' in weights_factory


def test_loaded_weights(weights_factory):
    assert len(weights_factory) == 5
