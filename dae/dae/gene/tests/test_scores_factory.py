def test_score_default(scores_factory):
    assert scores_factory is not None


def test_score_raw(scores_factory):
    assert scores_factory["score_raw"] is not None

    raw = scores_factory["score_raw"]
    assert raw.df is not None

    assert "score_raw" in raw.df.columns


def test_scores_has_score_raw(scores_factory):
    assert "score_raw" in scores_factory


def test_loaded_scores(scores_factory):
    assert len(scores_factory.scores) == 3
