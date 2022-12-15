# pylint: disable=W0621,C0114,C0116,W0212,W0613

import textwrap
import pathlib
import pytest
import yaml
import pysam

from dask.distributed import Client  # type: ignore

from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.histogram import HistogramBuilder
from dae.genomic_resources.testing import \
    tabix_to_resource, \
    setup_directories, setup_tabix, build_filesystem_test_repository


@pytest.fixture(scope="module")
def dask_client():
    client = Client(n_workers=4, threads_per_worker=1)
    yield client
    client.close()


@pytest.fixture
def repo_fixture(tmp_path_factory):
    # the following config is missing min/max for phastCons100way
    root_path = tmp_path_factory.mktemp("repo_fixture")
    setup_directories(root_path, {
        "one": {
            GR_CONF_FILE_NAME: textwrap.dedent("""
                type: position_score
                table:
                    filename: data.txt.gz
                    format: tabix
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
    setup_tabix(
        root_path / "one" / "data.txt.gz",
        """
        #chrom  pos_begin  pos_end  s1    s2
        1       10         15       0.02  1.02
        1       17         19       0.03  1.03
        1       22         25       0.04  1.04
        2       5          80       0.01  2.01
        2       10         11       0.02  2.02
        """, seq_col=0, start_col=1, end_col=2)
    return build_filesystem_test_repository(root_path)


def test_double_build_histograms_without_change(repo_fixture, dask_client):

    resource = repo_fixture.get_resource("one")
    hbuilder = HistogramBuilder(resource)
    hists = hbuilder.update(dask_client)
    hbuilder.save(hists, "histograms")

    repo_fixture.proto.invalidate()
    resource = repo_fixture.get_resource("one")
    hbuilder2 = HistogramBuilder(resource)

    # All histograms are already calculated and update should return
    # empty list.
    # That's why we pass a None for the client as it shouldn't be used.
    hists2 = hbuilder2.update(None, "histograms")

    assert len(hists2) == 0


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


def one_tabix_index_update(repo):
    root_path = pathlib.Path(repo.proto.root_path)
    # pylint: disable=no-member
    pysam.tabix_index(
        str(root_path / "one" / "data.txt.gz"),
        seq_col=0, start_col=1, end_col=2, line_skip=1, force=True)
    proto = repo.proto
    res = proto.get_resource("one")
    proto.save_manifest(res, proto.build_manifest(res))
    proto.invalidate()
    proto.build_content_file()


def test_tabix_index_update(repo_fixture):
    res = repo_fixture.get_resource("one")
    manifest = res.get_manifest()

    one_tabix_index_update(repo_fixture)

    res_u = repo_fixture.get_resource("one")
    manifest_u = res_u.get_manifest()
    manifest_u = repo_fixture.proto.update_manifest(res_u)

    assert manifest != manifest_u

    assert manifest["data.txt.gz"] == manifest_u["data.txt.gz"]
    assert manifest["data.txt.gz.tbi"] != manifest_u["data.txt.gz.tbi"]


def test_build_hashes_with_changed_tabix_index(repo_fixture):

    # Given
    res = repo_fixture.get_resource("one")
    hbuilder = HistogramBuilder(res)
    hashes = hbuilder._build_hashes()

    # When
    one_tabix_index_update(repo_fixture)
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
        res, "data.txt.gz"
    )
    repo_fixture.invalidate()
    res = repo_fixture.get_resource("one")

    # Then
    hbuilder = HistogramBuilder(res)
    hashes2 = hbuilder._build_hashes()

    assert hashes != hashes2
