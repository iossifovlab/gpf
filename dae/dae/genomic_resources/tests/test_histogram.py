# pylint: disable=W0621,C0114,C0116,W0212,W0613

import os

import pytest
import numpy as np

from dask.distributed import Client  # type: ignore

from dae.genomic_resources.repository import GR_CONF_FILE_NAME, \
    GenomicResource
from dae.genomic_resources.histogram import Histogram, \
    HistogramBuilder, load_histograms
from dae.genomic_resources.testing import build_test_resource, \
    build_testing_repository
from dae.genomic_resources.test_tools import convert_to_tab_separated


def test_histogram_simple_input():
    hist = Histogram(None, None, 10, 0, 10, "linear", "linear")
    hist.set_empty()
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
    hist = Histogram(None, None, 4, 0, 1000, "log", "linear", x_min_log=1)
    hist.set_empty()
    assert (hist.bins == np.array([0, 1, 10, 100, 1000])).all()

    hist.add_value(0)
    assert (hist.bars == np.array([1, 0, 0, 0])).all()

    for i in [0.5, 2, 10, 200]:
        hist.add_value(i)
    assert (hist.bars == np.array([2, 1, 1, 1])).all()

    hist.add_value(2000)
    hist.add_value(-1)
    assert (hist.bars == np.array([2, 1, 1, 1])).all()


def test_histogram_merge():
    hist1 = Histogram(
        np.arange(0, 11),
        np.array([0, 0, 0, 1, 0, 0, 0, 1, 0, 2]),
        10, 0, 10, "linear", "linear"
    )
    hist2 = Histogram(
        np.arange(0, 11),
        np.array([0, 0, 0, 0, 0, 1, 0, 1, 0, 0]),
        10, 0, 10, "linear", "linear"
    )

    hist = Histogram.merge(hist1, hist2)
    assert (hist.bars == np.array([0, 0, 0, 1, 0, 1, 0, 2, 0, 2])).all()


@pytest.fixture(scope="module")
def client():
    client = Client(n_workers=4, threads_per_worker=1)
    yield client
    client.close()


@pytest.mark.parametrize("region_size", [1, 10, 10000])
def test_histogram_builder_position_resource(tmp_path, client, region_size):
    res: GenomicResource = build_test_resource(
        content={
            GR_CONF_FILE_NAME: """
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
                      max: 4
                """,
            "data.mem": convert_to_tab_separated("""
                chrom  pos_begin  pos_end  s1    s2
                1      10         15       0.02  -1
                1      17         19       0.03  0
                1      22         25       0.46  EMPTY
                2      5          80       0.01  3
                2      10         11       0.02  3
                """)
        },
        scheme="file",
        root_path=str(tmp_path))

    hbuilder = HistogramBuilder(res)
    hists = hbuilder.build(client, region_size=region_size)
    assert len(hists) == 2

    phast_cons_100way_hist = hists["phastCons100way"]
    assert len(phast_cons_100way_hist.bars) == 100
    assert phast_cons_100way_hist.bars[0] == 0
    assert phast_cons_100way_hist.bars[1] == 76  # region [5-80]
    assert phast_cons_100way_hist.bars[2] == 8  # region [10-15] and [10-11]
    assert phast_cons_100way_hist.bars[3] == 3  # region [17-19]
    assert phast_cons_100way_hist.bars[4] == 0
    assert phast_cons_100way_hist.bars[46] == 4  # region [22-24]
    assert phast_cons_100way_hist.bars.sum() == (76 + 8 + 3 + 4)

    phast_cons_5way_hist = hists["phastCons5way"]
    assert len(phast_cons_5way_hist.bars) == 4
    assert phast_cons_5way_hist.bars[0] == 3  # region [17-19]
    assert phast_cons_5way_hist.bars[3] == 76 + 2  # region [5-80] and [10-11]
    assert phast_cons_5way_hist.bars.sum() == (76 + 2 + 3)


def test_histogram_builder_allele_resource(client, tmp_path):
    res: GenomicResource = build_test_resource(
        content={
            GR_CONF_FILE_NAME: """
                type: allele_score
                table:
                    filename: data.mem
                scores:
                    - id: freq
                      type: float
                      desc: ""
                      name: freq
                histograms:
                    - score: freq
                      bins: 100
                      min: 0
                      max: 1
                """,
            "data.mem": convert_to_tab_separated("""
                chrom  pos_begin  reference  alternative  freq
                1      10         A          G            0.02
                1      10         A          C            0.03
                1      10         A          A            0.04
                1      16         CA         G            0.03
                1      16         C          T            0.04
                1      16         C          A            0.05
                2      16         CA         G            0.03
                2      16         C          T            EMPTY
                2      16         C          A            0.05
            """)
        },
        scheme="file",
        root_path=str(tmp_path))

    hbuilder = HistogramBuilder(res)
    hists = hbuilder.build(client)
    assert len(hists) == 1

    freq_hist = hists["freq"]
    assert len(freq_hist.bars) == 100
    assert freq_hist.bars[0] == 0
    assert freq_hist.bars[2] == 1  # region [10]
    assert freq_hist.bars[3] == 3  # region [10, 16, 16]
    assert freq_hist.bars[4] == 2  # region [10, 16]
    assert freq_hist.bars[5] == 2  # region [16, 16]
    assert freq_hist.bars.sum() == (1 + 3 + 2 + 2)


def test_histogram_builder_np_resource(client, tmp_path):
    res: GenomicResource = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            GR_CONF_FILE_NAME: """
                type: np_score
                table:
                    filename: data.mem
                scores:
                    - id: cadd_raw
                      type: float
                      desc: ""
                      name: s1
                    - id: cadd_test
                      type: int
                      position_aggregator: max
                      nucleotide_aggregator: mean
                      na_values: "-1"
                      desc: ""
                      name: s2
                histograms:
                    - score: cadd_raw
                      bins: 100
                      min: 0
                      max: 1
                    - score: cadd_test
                      bins: 4
                      min: 0
                      max: 4
            """,
            "data.mem": """
                chrom  pos_begin  pos_end  reference  alternative  s1    s2
                1      10         15       A          G            0.02  2
                1      10         15       A          C            0.03  -1
                1      10         15       A          T            0.04  4
                1      16         19       C          G            0.03  3
                1      16         19       C          T            0.04  EMPTY
                1      16         19       C          A            0.05  0
                2      16         19       C          A            0.03  3
                2      16         19       C          T            0.04  3
                2      16         19       C          G            0.05  4
            """
        })
    hbuilder = HistogramBuilder(res)
    hists = hbuilder.build(client)
    assert len(hists) == 2

    cadd_raw_hist = hists["cadd_raw"]
    assert len(cadd_raw_hist.bars) == 100
    assert cadd_raw_hist.bars[2] == 6  # region [10-15]
    assert cadd_raw_hist.bars[3] == 14  # region [10-15], 2x[16-19]
    assert cadd_raw_hist.bars[4] == 14  # region [10-15], 2x[16-19]
    assert cadd_raw_hist.bars[5] == 8  # region 2x[16-19]
    assert cadd_raw_hist.bars.sum() == (6 + 14 + 14 + 8)

    cadd_test_hist = hists["cadd_test"]
    assert len(cadd_test_hist.bars) == 4
    assert cadd_test_hist.bars[0] == 4  # region [16-19]
    assert cadd_test_hist.bars[2] == 6  # region [10-15]
    assert cadd_test_hist.bars[3] == 22  # region [10-15]
    assert cadd_test_hist.bars.sum() == (4 + 6 + 22)


@pytest.mark.parametrize("region_size", [1, 10, 10000])
def test_histogram_builder_no_explicit_min_max(tmp_path, client, region_size):
    res: GenomicResource = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            GR_CONF_FILE_NAME: """
                type: position_score
                table:
                    filename: data.mem
                scores:
                    - id: phastCons100way
                      type: float
                      desc: "The phastCons computed over the tree of 100 \
                              verterbarte species"
                      name: s1
                histograms:
                    - score: phastCons100way
                      bins: 100
            """,
            "data.mem": convert_to_tab_separated("""
                chrom  pos_begin  pos_end  s1
                1      10         15       0.0
                1      17         19       0.03
                1      22         25       0.46
                2      5          80       0.01
                2      10         11       1.0
                3      5          17       1.0
                3      18         20       0.01
            """)
        })
    hbuilder = HistogramBuilder(res)
    hists = hbuilder.build(client, region_size=region_size)
    assert len(hists) == 1

    assert hists["phastCons100way"].x_min == 0
    assert hists["phastCons100way"].x_max == 1


def test_histogram_builder_save(tmp_path, client):
    res: GenomicResource = build_test_resource(
        content={
            GR_CONF_FILE_NAME: """
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
                      max: 4
                """,
            "data.mem": convert_to_tab_separated("""
                chrom  pos_begin  pos_end  s1    s2
                1      10         15       0.02  -1
                1      17         19       0.03  0
                1      22         25       0.46  EMPTY
                2      5          80       0.01  3
                2      10         11       0.02  3
                """)
        },
        scheme="file",
        root_path=str(tmp_path))

    hbuilder = HistogramBuilder(res)
    hists = hbuilder.build(client)
    hbuilder.save(hists, "")

    proto = res.proto
    filesystem = proto.filesystem
    res_url = proto.get_resource_url(res)

    assert filesystem.exists(
        os.path.join(res_url, "phastCons100way.csv"))
    assert filesystem.exists(
        os.path.join(res_url, "phastCons100way.metadata.yaml"))
    assert filesystem.exists(
        os.path.join(res_url, "phastCons100way.png"))

    assert filesystem.exists(
        os.path.join(res_url, "phastCons5way.csv"))
    assert filesystem.exists(
        os.path.join(res_url, "phastCons5way.metadata.yaml"))
    assert filesystem.exists(
        os.path.join(res_url, "phastCons5way.png"))

    # assert the manifest file is updated
    proto.save_manifest(res, proto.update_manifest(res))
    manifest = res.get_manifest()
    for score_id in ["phastCons5way", "phastCons100way"]:
        assert f"{score_id}.csv" in manifest
        assert f"{score_id}.metadata.yaml" in manifest
        assert f"{score_id}.png" in manifest


def test_building_already_calculated_histograms(tmp_path, client):
    # the following config is missing min/max for phastCons100way
    repo = build_testing_repository(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "one": {
                GR_CONF_FILE_NAME: """
                    type: position_score
                    table:
                        filename: data.mem
                    scores:
                        - id: phastCons100way
                          type: float
                          name: s1
                        - id: phastCons5way
                          type: int
                          position_aggregator: max
                          na_values: "-1"
                          name: s2
                    histograms:
                        - score: phastCons100way
                          bins: 100
                        - score: phastCons5way
                          bins: 4
                          min: 0
                          max: 4
                    """,
                "data.mem": convert_to_tab_separated("""
                    chrom  pos_begin  pos_end  s1    s2
                    1      10         15       0.02  -1
                    1      17         19       0.03  0
                    1      22         25       0.46  EMPTY
                    2      5          80       0.01  3
                    2      10         11       0.02  3
                    """)
            }
        })
    resource = repo.get_resource("one")
    hbuilder = HistogramBuilder(resource)
    hists = hbuilder.build(client)
    hbuilder.save(hists, "histograms")
    repo.invalidate()

    resource = repo.get_resource("one")
    hbuilder2 = HistogramBuilder(resource)

    # All histograms are already calculated and should return empty list.
    # That's why we pass a None for the client as it shouldn't be used.
    hists2 = hbuilder2.update(None, "histograms")

    assert len(hists2) == 0
    # for score, hist in hists.items():
    #     assert score in hists2
    #     assert (hist.bars == hists2[score].bars).all()
    #     assert (hist.bins == hists2[score].bins).all()


def test_load_histograms(tmp_path, client):
    repo = build_testing_repository(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "one": {
                GR_CONF_FILE_NAME: """
                    type: position_score
                    table:
                        filename: data.mem
                    scores:
                        - id: phastCons100way
                          type: float
                          name: s1
                        - id: phastCons5way
                          type: int
                          position_aggregator: max
                          na_values: "-1"
                          name: s2
                    histograms:
                        - score: phastCons100way
                          bins: 100
                        - score: phastCons5way
                          bins: 4
                          min: 0
                          max: 4
                    """,
                "data.mem": convert_to_tab_separated("""
                    chrom  pos_begin  pos_end  s1    s2
                    1      10         15       0.02  -1
                    1      17         19       0.03  0
                    1      22         25       0.46  EMPTY
                    2      5          80       0.01  3
                    2      10         11       0.02  3
                    """)
            }
        })

    res = repo.get_resource("one")
    hbuilder = HistogramBuilder(res)
    hists = hbuilder.build(client)
    hbuilder.save(hists, "histograms")

    loaded = load_histograms(repo, "one")

    # assert histograms are correctly loaded
    assert len(loaded) == len(hists)
    for score_id, hist in hists.items():
        actual = loaded[score_id]
        assert np.isclose(hist.bins, actual.bins).all()
        assert (hist.bars == actual.bars).all()
        assert hist.x_min == actual.x_min
        assert hist.x_max == actual.x_max


def test_histogram_builder_build_hashes_stable(tmp_path):
    res: GenomicResource = build_test_resource(
        content={
            GR_CONF_FILE_NAME: """
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
                      max: 4
                """,
            "data.mem": convert_to_tab_separated("""
                chrom  pos_begin  pos_end  s1    s2
                1      10         15       0.02  -1
                1      17         19       0.03  0
                1      22         25       0.46  EMPTY
                2      5          80       0.01  3
                2      10         11       0.02  3
                """)
        },
        scheme="file",
        root_path=str(tmp_path))

    hbuilder = HistogramBuilder(res)
    hashes = hbuilder._build_hashes()
    assert len(hashes) == 2

    hashes2 = hbuilder._build_hashes()
    assert len(hashes2) == 2
    assert hashes["phastCons100way"] == hashes2["phastCons100way"]
    assert hashes["phastCons5way"] == hashes2["phastCons5way"]
    assert hashes2["phastCons100way"] != hashes2["phastCons5way"]

    hashes3 = hbuilder._build_hashes()
    assert len(hashes3) == 2
    assert hashes["phastCons100way"] == hashes3["phastCons100way"]
    assert hashes["phastCons5way"] == hashes3["phastCons5way"]
    assert hashes3["phastCons100way"] != hashes3["phastCons5way"]
