# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.testing import (
    setup_genome,
)


@pytest.fixture(scope="module")
def acgt_genome(
    tmp_path_factory: pytest.TempPathFactory,
) -> ReferenceGenome:
    root_path = tmp_path_factory.mktemp("genome")
    return setup_genome(
        root_path / "acgt_gpf" / "genome" / "allChr.fa",
        f"""
        >chr1
        {25 * "ACGT"}
        >chr2
        {25 * "ACGT"}
        >chr3
        {25 * "ACGT"}
        """,
    )
