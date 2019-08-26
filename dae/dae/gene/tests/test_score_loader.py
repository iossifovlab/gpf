def test_score_default(score_loader):
    assert score_loader is not None


def test_score_raw(score_loader):
    assert score_loader['SCORE-raw'] is not None

    raw = score_loader['SCORE-raw']
    assert raw.df is not None

    assert 'SCORE-raw' in raw.df.columns


def test_scores_has_score_raw(score_loader):
    assert 'SCORE-raw' in score_loader
