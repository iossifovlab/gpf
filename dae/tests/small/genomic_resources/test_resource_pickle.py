# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import pickle  # noqa: S403
import textwrap

import pytest
from dae.genomic_resources.fsspec_protocol import FsspecReadOnlyProtocol
from dae.genomic_resources.repository import (
    GenomicResourceRepo,
)
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.genomic_resources.testing import (
    convert_to_tab_separated,
    setup_directories,
)


@pytest.fixture
def grr_fixture(tmp_path: pathlib.Path) -> GenomicResourceRepo:
    root_path = tmp_path / "test_local_grr"

    setup_directories(
        root_path,
        {
            "one": {
                "genomic_resource.yaml": textwrap.dedent("""
                        type: position_score
                        table:
                            filename: data.txt
                        scores:
                        - id: score_one
                          type: float
                          name: score
                """),
                "data.txt": convert_to_tab_separated("""
                    chrom  pos_begin  score
                    chr1   4          1.01
                    chr1   54         1.02
                """),
            },
            "two": {
                "genomic_resource.yaml": textwrap.dedent("""
                        type: position_score
                        table:
                            filename: data.txt
                        scores:
                        - id: score_two
                          type: float
                          name: score
                """),
                "data.txt": convert_to_tab_separated("""
                    chrom  pos_begin  score
                    chr1   4          2.11
                    chr1   54         2.12
                """),
            },
            "three": {
                "genomic_resource.yaml": textwrap.dedent("""
                        type: position_score
                        table:
                            filename: data.txt
                        scores:
                        - id: score_three
                          type: float
                          name: score
                """),
                "data.txt": convert_to_tab_separated("""
                    chrom  pos_begin  score
                    chr1   4          3.11
                    chr1   54         3.12
                """),
            },
        },
    )
    return build_genomic_resource_repository({
        "id": "test_local",
        "type": "directory",
        "directory": str(root_path),
    })


def test_pickle_genomic_score(grr_fixture: GenomicResourceRepo) -> None:

    res_one = grr_fixture.get_resource("one")
    res_one_u = pickle.loads(pickle.dumps(res_one))
    assert res_one_u.get_type() == "position_score"
    assert res_one_u.resource_id == "one"

    assert isinstance(res_one.proto, FsspecReadOnlyProtocol)
    assert isinstance(res_one_u.proto, FsspecReadOnlyProtocol)

    assert res_one.proto._all_resources is not None
    assert len(res_one.proto._all_resources) == 3

    assert res_one_u.proto._all_resources is None
