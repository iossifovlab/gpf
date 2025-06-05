# pylint: disable=redefined-outer-name,C0114,C0116,protected-access,fixme

import pytest

from dae.genomic_resources.liftover_chain import (
    build_liftover_chain_from_resource,
)
from dae.genomic_resources.reference_genome import (
    build_reference_genome_from_resource,
)
from dae.genomic_resources.repository import GenomicResourceRepo


@pytest.mark.parametrize("schrom, spos, expected", [
    ("foo", 3, None),
    ("foo", 4, None),
    ("foo", 5, ("chrFoo", 1, "+", 4900)),
    ("foo", 6, ("chrFoo", 2, "+", 4900)),
    ("foo", 7, ("chrFoo", 3, "+", 4900)),
    ("foo", 14, ("chrFoo", 10, "+", 4900)),
    ("foo", 51, ("chrFoo", 47, "+", 4900)),
    ("foo", 52, ("chrFoo", 48, "+", 4900)),
    ("foo", 53, None),
    ("foo", 54, None),
    ("foo", 55, None),
    ("foo", 56, None),
    ("foo", 57, ("chrFoo", 49, "+", 4900)),
    ("foo", 58, ("chrFoo", 50, "+", 4900)),
    ("foo", 80, ("chrFoo", 72, "+", 4900)),
    ("foo", 103, ("chrFoo", 95, "+", 4900)),
    ("foo", 104, ("chrFoo", 96, "+", 4900)),
    ("foo", 105, None),
    ("bar", 5, ("chrBar", 1, "+", 4800)),
    ("bar", 52, ("chrBar", 48, "+", 4800)),
    ("bar", 53, None),
    ("bar", 60, None),
    ("bar", 61, ("chrBar", 49, "+", 4800)),
    ("bar", 108, ("chrBar", 96, "+", 4800)),
    ("bar", 109, None),
    ("bar", 112, None),
    ("baz", 5, ("chrBaz", 96, "-", 4700)),
    ("baz", 6, ("chrBaz", 95, "-", 4700)),
    ("baz", 51, ("chrBaz", 50, "-", 4700)),
    ("baz", 52, ("chrBaz", 49, "-", 4700)),
    ("baz", 53, None),
    ("baz", 56, None),
    ("baz", 57, ("chrBaz", 48, "-", 4700)),
    ("baz", 104, ("chrBaz", 1, "-", 4700)),
    ("baz", 105, None),
])
def test_liftover_chain_fixture(
        schrom: str,
        spos: int,
        expected: tuple[str, int, str, int] | None,
        liftover_grr_fixture: GenomicResourceRepo) -> None:
    res = liftover_grr_fixture.get_resource("liftover_chain")
    liftover_chain = build_liftover_chain_from_resource(res)

    res = liftover_grr_fixture.get_resource("target_genome")
    target_genome = build_reference_genome_from_resource(res).open()
    res = liftover_grr_fixture.get_resource("source_genome")
    source_genome = build_reference_genome_from_resource(res).open()

    assert liftover_chain is not None
    liftover_chain.open()
    lo_coordinates = liftover_chain.convert_coordinate(schrom, spos)
    assert lo_coordinates == expected

    if expected is not None:
        sseq = source_genome.get_sequence(schrom, spos, spos)
        chrom, pos, _, _ = expected
        tseq = target_genome.get_sequence(chrom, pos, pos)
        assert sseq == tseq
