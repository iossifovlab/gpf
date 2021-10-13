import io
import numpy as np

from dae.tools.generate_vcf_score_histogram import ScoreHistogram, \
    Range, load_domain_ranges, store_domain_ranges


def test_score_histogram_linear():
    hist = ScoreHistogram("linear", 10, Range(0, 1))

    assert len(hist.bins) == 11
    assert len(hist.bars) == 11


def test_score_histogram_log():
    hist = ScoreHistogram("log", 10, Range(1, 2))

    assert len(hist.bins) == 11
    assert len(hist.bars) == 11


def test_score_histogram_log_zero():
    hist = ScoreHistogram("log", 10, Range(0, 1))

    assert len(hist.bins) == 11
    assert len(hist.bars) == 11


def test_update_histogram_linear():
    hist = ScoreHistogram("linear", 10, Range(0, 10))
    for v in range(11):
        hist.update_histogram(v)

    assert np.all(hist.bars == 1.0)


def test_merge_histograms():
    hist1 = ScoreHistogram("linear", 10, Range(0, 10))
    hist2 = ScoreHistogram("linear", 10, Range(0, 10))
    for v in range(11):
        hist1.update_histogram(v)
        hist2.update_histogram(v)

    assert np.all(hist1.bars == 1.0)
    assert np.all(hist2.bars == 1.0)

    hist1.merge(hist2)
    assert np.all(hist1.bars == 2.0)


def test_store_domain_ranges():
    domain_ranges = {"AC": Range(0, 100_000), "AN": Range(2, 99_000)}
    output = io.StringIO()

    store_domain_ranges(domain_ranges, output)
    print(output.getvalue())

    infile = io.StringIO(output.getvalue())

    result = load_domain_ranges(infile)
    print(result)

    assert result["AC"].min == domain_ranges["AC"].min
    assert result["AC"].max == domain_ranges["AC"].max
    assert result["AN"].min == domain_ranges["AN"].min
    assert result["AN"].max == domain_ranges["AN"].max
