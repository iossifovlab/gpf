from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo
import pytest
import os
from dae.genomic_resources.repository import GR_CONF_FILE_NAME, GenomicResource
from dae.genomic_resources.score_statistics import Histogram, \
    HistogramBuilder, load_histograms
from dae.genomic_resources.test_tools import build_a_test_resource
from dae.genomic_resources.dir_repository import GenomicResourceDirRepo
from dae.genomic_resources.cached_repository import GenomicResourceCachedRepo
import numpy as np


@pytest.mark.xfail
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


@pytest.mark.xfail
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


@pytest.fixture(scope="module")
def client():
    from dask.distributed import Client  # type: ignore

    client = Client(n_workers=4, threads_per_worker=1)
    yield client
    client.close()


@pytest.mark.parametrize("region_size", [1, 10, 10000])
def test_histogram_builder_position_resource(client, region_size):
    res: GenomicResource = build_a_test_resource(position_score_test_config)
    hbuilder = HistogramBuilder(res)
    hists = hbuilder.build(client, region_size=region_size)
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


def test_histogram_builder_allele_resource(client):
    res: GenomicResource = build_a_test_resource({
        GR_CONF_FILE_NAME: '''
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
                  max: 1''',
        "data.mem": '''
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
        '''
    })
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


def test_histogram_builder_np_resource(client):
    res: GenomicResource = build_a_test_resource({
        GR_CONF_FILE_NAME: '''
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
        ''',
        "data.mem": '''
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
        '''
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
def test_histogram_builder_no_explicit_min_max(client, region_size):
    res: GenomicResource = build_a_test_resource({
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
            histograms:
                - score: phastCons100way
                  bins: 100''',
        "data.mem": '''
            chrom  pos_begin  pos_end  s1
            1      10         15       0.0
            1      17         19       0.03
            1      22         25       0.46
            2      5          80       0.01
            2      10         11       1.0
            3      5          17       1.0
            3      18         20       0.01
            '''
    })
    hbuilder = HistogramBuilder(res)
    hists = hbuilder.build(client, region_size=region_size)
    assert len(hists) == 1

    assert hists["phastCons100way"].x_min == 0
    assert hists["phastCons100way"].x_max == 1


def test_histogram_builder_save(tmpdir, client):
    for fn, content in position_score_test_config.items():
        with open(os.path.join(tmpdir, fn), 'wt') as f:
            f.write(content)

    repo = GenomicResourceDirRepo("", tmpdir)
    res = repo.get_resource("")
    hbuilder = HistogramBuilder(res)
    hists = hbuilder.build(client)
    hbuilder.save(hists, "")

    files = os.listdir(tmpdir)
    # 2 config, 2 histograms, 2 metadatas, 1 manifest, 2 png images
    assert len(files) == 9

    # assert the manifest file is updated
    manifest = repo.load_manifest(res)
    for score_id in ['phastCons5way', 'phastCons100way']:
        assert f'{score_id}.csv' in manifest
        assert f'{score_id}.metadata.yaml' in manifest


def test_building_already_calculated_histograms(tmpdir, client):
    # the following config is missing min/max for phastCons100way
    embedded_repo = GenomicResourceEmbededRepo("", {
        GR_CONF_FILE_NAME: '''
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
                  max: 4''',
        "data.mem": '''
            chrom  pos_begin  pos_end  s1    s2
            1      10         15       0.02  -1
            1      17         19       0.03  0
            1      22         25       0.46  EMPTY
            2      5          80       0.01  3
            2      10         11       0.02  3
            '''
    })
    repo = GenomicResourceDirRepo("", tmpdir)
    repo.store_all_resources(embedded_repo)

    resource = repo.get_resource("")
    hbuilder = HistogramBuilder(resource)
    hists = hbuilder.build(client)
    os.makedirs(os.path.join(tmpdir, "histograms"))
    hbuilder.save(hists, "histograms")

    # create a new repo to ensure clean start
    repo = GenomicResourceDirRepo("", tmpdir)
    resource = repo.get_resource("")

    hbuilder2 = HistogramBuilder(resource)
    # All histograms are already calculated and should simply be loaded
    # from disk without any actual computations being carried out.
    # That's why we pass a None for the client as it shouldn't be used.
    hists2 = hbuilder2.build(None, "histograms")

    assert len(hists) == len(hists2)
    for score, hist in hists.items():
        assert score in hists2
        assert (hist.bars == hists2[score].bars).all()
        assert np.isclose(hist.bins, hists2[score].bins).all()


def test_load_histograms(tmpdir, client):
    repo_dir = os.path.join(tmpdir, "repo")
    os.makedirs(repo_dir)
    for fn, content in position_score_test_config.items():
        with open(os.path.join(repo_dir, fn), 'wt', encoding="utf8") as f:
            f.write(content)

    repo = GenomicResourceDirRepo("", repo_dir)
    res = repo.get_resource("")
    hbuilder = HistogramBuilder(res)
    hists = hbuilder.build(client)

    os.makedirs(os.path.join(repo_dir, "histograms"))
    hbuilder.save(hists, "histograms")

    cache_dir = os.path.join(tmpdir, "cache")
    os.makedirs(cache_dir)
    cache_repo = GenomicResourceCachedRepo(repo, cache_dir)

    loaded = load_histograms(cache_repo, "")

    # assert histograms are correctly loaded
    assert len(loaded) == len(hists)
    for score_id, hist in hists.items():
        actual = loaded[score_id]
        assert np.isclose(hist.bins, actual.bins).all()
        assert (hist.bars == actual.bars).all()
        assert hist.x_min == actual.x_min
        assert hist.x_max == actual.x_max

    # assert nothing is cached
    files = os.listdir(cache_dir)
    assert len(files) == 0


def test_histogram_builder_build_hashes():
    res: GenomicResource = build_a_test_resource(position_score_test_config)
    hbuilder = HistogramBuilder(res)
    hashes = hbuilder._build_hashes()
    assert len(hashes) == 2

    hashes_again = hbuilder._build_hashes()
    assert hashes["phastCons100way"] == hashes_again["phastCons100way"]
    assert hashes["phastCons5way"] == hashes_again["phastCons5way"]
    assert hashes["phastCons100way"] != hashes["phastCons5way"]
