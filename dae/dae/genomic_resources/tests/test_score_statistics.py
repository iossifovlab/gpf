from dae.genomic_resources.repository import GR_CONF_FILE_NAME, GenomicResource
from dae.genomic_resources.score_statistics import Histogram, HistogramBuilder
from dae.genomic_resources.test_tools import build_a_test_resource
import numpy as np


def test_histogram_simple_input():
    hist = Histogram(10, 0, 10, "linear", "linear")
    assert (hist.bins == np.arange(0, 11)).all()

    hist.add_value(0)
    assert (hist.bars == np.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])).all()

    for i in range(1, 11):
        hist.add_value(i)
    assert (hist.bars == np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 2])).all()

    hist.add_value(12)
    hist.add_value(-1)
    assert (hist.bars == np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 2])).all()


def test_histogram_log_scale():
    hist = Histogram(4, 0, 1000, "log", "linear", x_min_log=1)
    assert (hist.bins == np.array([0, 1, 10, 100, 1000])).all()

    hist.add_value(0)
    assert (hist.bars == np.array([1, 0, 0, 0])).all()

    for i in [0.5, 2, 10, 200]:
        hist.add_value(i)
    assert (hist.bars == np.array([2, 1, 1, 1])).all()

    hist.add_value(2000)
    hist.add_value(-1)
    assert (hist.bars == np.array([2, 1, 1, 1])).all()


position_score_test_config = {
    GR_CONF_FILE_NAME: '''
        type: position_score
        table:
            filename: data.mem
        scores:
            - id: phastCons100way
              type: float
              desc: "The phastCons computed over the tree of 100 \
                    verterbarte species"
              name: s1
            - id: phastCons5way
              type: int
              position_aggregator: max
              na_values: "-1"
              desc: "The phastCons computed over the tree of 5 \
                    verterbarte species"
              name: s2
        histograms:
            - score: phastCons100way
              bins: 100
              min: 0
              max: 1
            - score: phastCons5way
              bins: 4
              min: 0
              max: 4''',
    "data.mem": '''
        chrom  pos_begin  pos_end  s1    s2
        1      10         15       0.02  -1
        1      17         19       0.03  0
        1      22         25       0.46  EMPTY
        2      5          80       0.01  3
        2      10         11       0.02  3
        '''
}


def test_histogram_builder_position_resource():
    res: GenomicResource = build_a_test_resource(position_score_test_config)
    hbuilder = HistogramBuilder()
    hists = hbuilder.build(res)
    assert len(hists) == 2

    phastCons100way_hist = hists["phastCons100way"]
    assert len(phastCons100way_hist.bars) == 100
    assert phastCons100way_hist.bars[0] == 0
    assert phastCons100way_hist.bars[1] == 76  # region [5-80]
    assert phastCons100way_hist.bars[2] == 8  # region [10-15] and [10-11]
    assert phastCons100way_hist.bars[3] == 3  # region [17-19]
    assert phastCons100way_hist.bars[4] == 0
    assert phastCons100way_hist.bars[46] == 4  # region [22-24]
    assert phastCons100way_hist.bars.sum() == (76 + 8 + 3 + 4)

    phastCons5way_hist = hists["phastCons5way"]
    assert len(phastCons5way_hist.bars) == 4
    assert phastCons5way_hist.bars[0] == 3  # region [17-19]
    assert phastCons5way_hist.bars[3] == 76 + 2  # region [5-80] and [10-11]
    assert phastCons5way_hist.bars.sum() == (76 + 2 + 3)


def test_histogram_builder_save(tmpdir):
    res: GenomicResource = build_a_test_resource(position_score_test_config)
    hbuilder = HistogramBuilder()
    hists = hbuilder.build(res)
    hbuilder.save(hists, tmpdir)
