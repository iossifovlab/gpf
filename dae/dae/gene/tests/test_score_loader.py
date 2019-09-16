def test_score_default(score_loader):
    assert score_loader is not None


def test_score_raw(score_loader):
    assert score_loader['score_raw'] is not None

    raw = score_loader['score_raw']
    assert raw.df is not None

    assert 'score_raw' in raw.df.columns


def test_scores_has_score_raw(score_loader):
    assert 'score_raw' in score_loader


def test_loaded_scores(score_loader):
    assert len(score_loader.scores) == 3
