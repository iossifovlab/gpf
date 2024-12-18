# pylint: disable=W0621,C0114,C0116,W0212,W0613

from collections.abc import Callable

import pytest

from dae.genomic_resources.fsspec_protocol import build_fsspec_protocol
from dae.genomic_resources.liftover_chain import (
    build_liftover_chain_from_resource,
    build_liftover_chain_from_resource_id,
)
from dae.genomic_resources.repository import (
    GenomicResourceProtocolRepo,
    GenomicResourceRepo,
)


@pytest.mark.parametrize("pos,expected_chrom,expected_pos,expected_strand", [
    (100_000, "1", 100_000, "+"),
    (180_000, "16", 90_188_903, "-"),
    (190_000, "2", 114_351_527, "-"),
    (260_000, "1", 229_751, "+"),
])
def test_liftover_chain_resource(
        fixture_dirname: Callable[[str], str],
        pos: int, expected_chrom: str, expected_pos: int,
        expected_strand: str) -> None:

    dirname = fixture_dirname("genomic_resources")
    proto = build_fsspec_protocol("d", dirname)
    repo = GenomicResourceProtocolRepo(proto)

    chain_resource = repo.get_resource(
        "hg38/hg38tohg19")
    assert chain_resource
    chain = build_liftover_chain_from_resource(chain_resource)
    chain.open()

    out = chain.convert_coordinate("chr1", pos)
    assert out is not None
    assert out[0] == expected_chrom
    assert out[1] == expected_pos
    assert out[2] == expected_strand


def test_build_liftover_chain_from_resource_id(
    liftover_grr_fixture: GenomicResourceRepo,
) -> None:
    liftover_chain = build_liftover_chain_from_resource_id(
        "liftover_chain", liftover_grr_fixture)
    assert liftover_chain is not None
