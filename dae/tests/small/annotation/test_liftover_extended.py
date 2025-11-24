# pylint: disable=redefined-outer-name,C0114,C0116,protected-access,fixme,R0917
import pathlib
import textwrap

import pytest
from dae.genomic_resources.liftover_chain import (
    build_liftover_chain_from_resource,
)
from dae.genomic_resources.reference_genome import (
    build_reference_genome_from_resource,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    convert_to_tab_separated,
    setup_directories,
    setup_genome,
    setup_gzip,
)


@pytest.fixture
def liftover_data(
    tmp_path: pathlib.Path,
) -> GenomicResourceRepo:
    setup_genome(
        tmp_path / "source_genome" / "genome.fa",
        textwrap.dedent("""
            >chrA
            ATCGATCG
            ATCG
            """),
    )
    setup_genome(
        tmp_path / "target_genome" / "genome.fa",
        textwrap.dedent("""
            >chrB
            ATCGATCG
            ATCG
            """),
    )
    setup_gzip(
        tmp_path / "liftover_chain" / "liftover.chain.gz",
        convert_to_tab_separated("""
        chain 100 chrA 12 + 0 12 chrB 12 + 0 12 1
        12 0 0
        0
        """),
    )
    setup_directories(tmp_path, {
        "source_genome": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: genome
                filename: genome.fa
            """),
        },
        "target_genome": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: genome
                filename: genome.fa
            """),
        },
        "liftover_chain": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: liftover_chain

                filename: liftover.chain.gz
            """),
        },
    })

    return build_filesystem_test_repository(tmp_path)


def test_check_liftover_resources(
    liftover_data: GenomicResourceRepo,
) -> None:
    source_genome = build_reference_genome_from_resource(
        liftover_data.get_resource("source_genome"),
    ).open()
    assert source_genome is not None
    assert "chrA" in source_genome.chromosomes

    target_genome = build_reference_genome_from_resource(
        liftover_data.get_resource("target_genome"),
    ).open()
    assert target_genome is not None
    assert "chrB" in target_genome.chromosomes

    liftover_chain = build_liftover_chain_from_resource(
        liftover_data.get_resource("liftover_chain"),
    ).open()
    assert liftover_chain is not None
    mapped = liftover_chain.convert_coordinate("chrA", 2)
    assert mapped == ("chrB", 2, "+", 100)
