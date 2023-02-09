# pylint: disable=W0621,C0114,C0116,W0212,W0613

import textwrap
import pathlib
import pytest
import yaml
import pysam

from dask.distributed import Client  # type: ignore

from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.testing import \
    setup_directories, setup_tabix, build_filesystem_test_protocol


@pytest.fixture(scope="module")
def dask_client():
    client = Client(n_workers=4, threads_per_worker=1)
    yield client
    client.close()


@pytest.fixture
def proto_fixture(tmp_path):
    # the following config is missing min/max for phastCons100way
    setup_directories(tmp_path, {
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
        tmp_path / "one" / "data.txt.gz",
        """
        #chrom  pos_begin  pos_end  s1    s2
        1       10         15       0.02  1.02
        1       17         19       0.03  1.03
        1       22         25       0.04  1.04
        2       5          80       0.01  2.01
        2       10         11       0.02  2.02
        """, seq_col=0, start_col=1, end_col=2)
    return build_filesystem_test_protocol(tmp_path)


def one_tabix_index_update(proto):
    root_path = pathlib.Path(proto.root_path)
    # pylint: disable=no-member
    pysam.tabix_index(
        str(root_path / "one" / "data.txt.gz"),
        seq_col=0, start_col=1, end_col=2, line_skip=1, force=True)
    res = proto.get_resource("one")
    proto.save_manifest(res, proto.build_manifest(res))
    proto.invalidate()
    proto.build_content_file()


def test_tabix_index_update(proto_fixture):
    res = proto_fixture.get_resource("one")
    manifest = res.get_manifest()

    one_tabix_index_update(proto_fixture)

    res_u = proto_fixture.get_resource("one")
    manifest_u = res_u.get_manifest()
    manifest_u = proto_fixture.update_manifest(res_u)

    assert manifest != manifest_u

    assert manifest["data.txt.gz"] == manifest_u["data.txt.gz"]
    assert manifest["data.txt.gz.tbi"] != manifest_u["data.txt.gz.tbi"]
