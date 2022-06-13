# pylint: disable=redefined-outer-name,C0114,C0116,protected-access
import textwrap
import pytest
import yaml

from dask.distributed import Client  # type: ignore

from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.score_statistics import \
    HistogramBuilder
from dae.genomic_resources.testing import \
    build_testing_repository, tabix_to_resource


@pytest.fixture(scope="module")
def dask_client():
    client = Client(n_workers=4, threads_per_worker=1)
    yield client
    client.close()


@pytest.fixture
def repo_fixture(tmp_path, tabix_file):
    # the following config is missing min/max for phastCons100way
    repo = build_testing_repository(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "one": {
                GR_CONF_FILE_NAME: textwrap.dedent("""
                    type: position_score
                    table:
                        filename: data.bgz
                    scores:
                        - id: phastCons100way
                          type: float
                          name: s1
                    histograms:
                        - score: phastCons100way
                          bins: 100
                    """),
            }
        })
    resource = repo.get_resource("one")
    tabix_to_resource(
        tabix_file(
            """
            #chrom  pos_begin  pos_end  s1    s2
            1       10         15       0.02  1.02
            1       17         19       0.03  1.03
            1       22         25       0.04  1.04
            2       5          80       0.01  2.01
            2       10         11       0.02  2.02
            """, seq_col=0, start_col=1, end_col=2),
        resource, "data.bgz"
    )
    return repo


@pytest.fixture
def tabix_index_update(tabix_file):

    def builder(res):
        tabix_to_resource(
            tabix_file(
                """
                #chrom  pos_begin  pos_end  s1    s2
                1       10         15       0.02  1.02
                1       17         19       0.03  1.03
                1       22         25       0.04  1.04
                2       5          80       0.01  2.01
                2       10         11       0.02  2.02
                """, seq_col=0, start_col=1, end_col=2, line_skip=1),
            res, "data.bgz"
        )

    return builder


def test_double_build_histograms_without_change(repo_fixture, dask_client):

    resource = repo_fixture.get_resource("one")
    hbuilder = HistogramBuilder(resource)
    hists = hbuilder.build(dask_client)
    hbuilder.save(hists, "histograms")

    repo_fixture.proto.invalidate()
    resource = repo_fixture.get_resource("one")
    hbuilder2 = HistogramBuilder(resource)

    # All histograms are already calculated and should simply be loaded
    # from disk without any actual computations being carried out.
    # That's why we pass a None for the client as it shouldn't be used.
    hists2 = hbuilder2.build(None, "histograms")

    assert len(hists) == len(hists2)
    for score, hist in hists.items():
        assert score in hists2
        assert (hist.bars == hists2[score].bars).all()
        assert (hist.bins == hists2[score].bins).all()


def test_build_hashes_without_change(repo_fixture):

    resource = repo_fixture.get_resource("one")
    hbuilder = HistogramBuilder(resource)
    hashes = hbuilder._build_hashes()
    hashes2 = hbuilder._build_hashes()

    assert hashes == hashes2


def test_build_hashes_with_changed_description(repo_fixture):
    # Given
    res = repo_fixture.get_resource("one")
    hbuilder = HistogramBuilder(res)
    hashes = hbuilder._build_hashes()

    # When
    with res.open_raw_file(GR_CONF_FILE_NAME, "at") as outfile:
        outfile.write(
            textwrap.dedent("""

            meta: alabala
            """)
        )

    repo_fixture.invalidate()
    res = repo_fixture.get_resource("one")

    # Then
    hbuilder = HistogramBuilder(res)
    hashes2 = hbuilder._build_hashes()

    assert hashes == hashes2


def test_build_hashes_with_changed_histogram_config(repo_fixture):
    # Given
    res = repo_fixture.get_resource("one")
    hbuilder = HistogramBuilder(res)
    hashes = hbuilder._build_hashes()

    # When
    with res.open_raw_file(GR_CONF_FILE_NAME, "rt") as infile:
        config = yaml.safe_load(infile)
    config["histograms"][0]["min"] = 0
    config["histograms"][0]["max"] = 10
    with res.open_raw_file(GR_CONF_FILE_NAME, "wt") as outfile:
        outfile.write(yaml.safe_dump(config))

    repo_fixture.invalidate()
    res = repo_fixture.get_resource("one")

    # Then
    hbuilder = HistogramBuilder(res)
    hashes2 = hbuilder._build_hashes()

    assert hashes != hashes2


def test_build_hashes_with_changed_scores_config(repo_fixture):
    # Given
    res = repo_fixture.get_resource("one")
    hbuilder = HistogramBuilder(res)
    hashes = hbuilder._build_hashes()

    # When
    with res.open_raw_file(GR_CONF_FILE_NAME, "rt") as infile:
        config = yaml.safe_load(infile)
    config["scores"][0]["desc"] = "ala bala desc"
    with res.open_raw_file(GR_CONF_FILE_NAME, "wt") as outfile:
        outfile.write(yaml.safe_dump(config))

    repo_fixture.invalidate()
    res = repo_fixture.get_resource("one")

    # Then
    hbuilder = HistogramBuilder(res)
    hashes2 = hbuilder._build_hashes()

    assert hashes != hashes2


def test_tabix_index_update(repo_fixture, tabix_index_update):
    res = repo_fixture.get_resource("one")
    manifest = res.get_manifest()

    tabix_index_update(res)

    repo_fixture.invalidate()
    res_u = repo_fixture.get_resource("one")
    manifest_u = res_u.get_manifest()

    assert manifest != manifest_u

    assert manifest["data.bgz"] == manifest_u["data.bgz"]
    assert manifest["data.bgz.tbi"] != manifest_u["data.bgz.tbi"]


def test_build_hashes_with_changed_tabix_index(
        repo_fixture, tabix_index_update):

    # Given
    res = repo_fixture.get_resource("one")
    hbuilder = HistogramBuilder(res)
    hashes = hbuilder._build_hashes()

    # When
    tabix_index_update(res)
    repo_fixture.invalidate()
    res = repo_fixture.get_resource("one")

    # Then
    hbuilder = HistogramBuilder(res)
    hashes2 = hbuilder._build_hashes()

    assert hashes != hashes2


def test_build_hashes_with_changed_table(
        repo_fixture, tabix_file):

    # Given
    res = repo_fixture.get_resource("one")
    hbuilder = HistogramBuilder(res)
    hashes = hbuilder._build_hashes()

    # When
    tabix_to_resource(
        tabix_file(
            """
            #chrom  pos_begin  pos_end  s1    s2
            1       10         15       0.02  1.02
            """, seq_col=0, start_col=1, end_col=2),
        res, "data.bgz"
    )
    repo_fixture.invalidate()
    res = repo_fixture.get_resource("one")

    # Then
    hbuilder = HistogramBuilder(res)
    hashes2 = hbuilder._build_hashes()

    assert hashes != hashes2
