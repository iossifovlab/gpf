import os

from dae.gene.tests.conftest import fixtures_dir

from dae.gene.scores import Scores


def test_scores_default(score_config):
    config = score_config.genomic_scores.score_raw
    s = Scores(config)
    df = s.df

    assert df is not None

    assert "score_raw" in df.columns
    assert "scores" in df.columns


def test_scores(score_config):
    config = score_config.genomic_scores.score_raw_rankscore
    s = Scores(config)

    assert s.id == "score_raw_rankscore"
    assert s.desc == "SCORE raw rankscore"
    assert len(s.values()) == 101
    assert s.values()[0] == 42.24
    assert s.values()[-1] == 0.0
    assert len(s.get_scores()) == 101
    assert s.get_scores()[0] == 0.0
    assert s.get_scores()[-1] == 1.0
    assert s.xscale == "linear"
    assert s.yscale == "log"
    assert s.range == (10, 100)
    assert s.help_filename == os.path.join(
        fixtures_dir(), "genomicScores/score_raw_rankscore.md"
    )
