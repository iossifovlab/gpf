# pylint: disable=redefined-outer-name,C0114,C0116,protected-access,fixme

import textwrap

import pytest

from dae.annotation.annotatable import Annotatable, CNVAllele, Position, Region
from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.genomic_resources.liftover_chain import (
    build_liftover_chain_from_resource,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    convert_to_tab_separated,
    setup_directories,
    setup_genome,
    setup_gzip,
)


@pytest.fixture()
def fixture_repo(
        tmp_path_factory: pytest.TempPathFactory) -> GenomicResourceRepo:
    root_path = tmp_path_factory.mktemp("regions_effect_annotation")
    setup_directories(root_path, {
        "target_genome": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: genome
                filename: genome.fa
            """),
        },
        "source_genome": {
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
    setup_genome(
        root_path / "target_genome" / "genome.fa",
        textwrap.dedent(f"""
            >chr1
            {25 * 'ACGT'}
            >chr2
            {25 * 'ACGT'}
            """),
    )
    setup_genome(
        root_path / "source_genome" / "genome.fa",
        textwrap.dedent(f"""
            >1
            NNNN{12 * 'ACGT'}NNNN{12 * 'ACGT'}
            >2
            NNNN{12 * 'ACGT'}NNNN{12 * 'ACGT'}
            """),
    )
    setup_gzip(
        root_path / "liftover_chain" / "liftover.chain.gz",
        convert_to_tab_separated("""
        chain 4900 1 104 + 4 104 chr1 100 + 0 96 1
        48 4 0
        48 0 0
        0
        """),
    )

    return build_filesystem_test_repository(root_path)


@pytest.mark.parametrize("spos, expected", [
    (("1", 5), ("chr1", 1, "+", 4900)),
    (("1", 14), ("chr1", 10, "+", 4900)),
    (("1", 52), ("chr1", 48, "+", 4900)),
    (("1", 80), ("chr1", 72, "+", 4900)),
    (("1", 53), None),
    (("2", 56), None),
])
def test_liftover_chain_fixture(
        spos: tuple[str, int],
        expected: tuple[str, int, str, int] | None,
        fixture_repo: GenomicResourceRepo) -> None:
    res = fixture_repo.get_resource("liftover_chain")
    liftover_chain = build_liftover_chain_from_resource(res)

    assert liftover_chain is not None
    liftover_chain.open()

    lo_coordinates = liftover_chain.convert_coordinate(spos[0], spos[1])
    assert lo_coordinates == expected


@pytest.mark.parametrize("annotatable, expected", [
    (Position("1", 10), Position("chr1", 6)),
    (Region("1", 5, 19), Region("chr1", 1, 15)),
    (Region("1", 5, 52), Region("chr1", 1, 48)),
    (Region("1", 5, 53), None),
    (CNVAllele("1", 5, 52, CNVAllele.Type.LARGE_DELETION),
     CNVAllele("chr1", 1, 48, CNVAllele.Type.LARGE_DELETION)),
])
def test_liftover_annotator(
        annotatable: Annotatable,
        expected: Annotatable | None,
        fixture_repo: GenomicResourceRepo) -> None:

    pipeline_config = textwrap.dedent("""
        - liftover_annotator:
            source_genome: source_genome
            target_genome: target_genome
            chain: liftover_chain
            attributes:
            - source: liftover_annotatable
              internal: false
    """)

    pipeline = load_pipeline_from_yaml(pipeline_config, fixture_repo)

    with pipeline.open() as work_pipeline:
        result = work_pipeline.annotate(annotatable)
        print(annotatable, result)

    print(annotatable, result)
    assert result["liftover_annotatable"] == expected
