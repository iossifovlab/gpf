# pylint: disable=redefined-outer-name,C0114,C0116,protected-access,fixme

import textwrap
from typing import Optional

import pytest

from dae.genomic_resources.testing import \
    setup_directories, convert_to_tab_separated, setup_genome, \
    build_filesystem_test_repository, setup_gzip

from dae.genomic_resources.liftover_chain import \
    build_liftover_chain_from_resource
from dae.genomic_resources.repository import GenomicResourceRepo

from dae.annotation.annotatable import Region, Position, CNVAllele, Annotatable
from dae.annotation.annotation_factory import build_annotation_pipeline


@pytest.fixture
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
        }
    })
    setup_genome(
        root_path / "target_genome" / "genome.fa",
        textwrap.dedent(f"""
            >chr1
            {25 * 'AGCT'}
            >chr2
            {25 * 'AGCT'}
            """)
    )
    setup_genome(
        root_path / "source_genome" / "genome.fa",
        textwrap.dedent(f"""
            >1
            NNNN{12 * 'AGCT'}NNNN{12 * 'AGCT'}
            >2
            NNNN{12 * 'AGCT'}NNNN{12 * 'AGCT'}
            """)
    )
    setup_gzip(
        root_path / "liftover_chain" / "liftover.chain.gz",
        convert_to_tab_separated("""
        chain||4900||1||48||+||4||52||chr1||48||+||1||49||1
        48 0 0
        0
        chain||4900||1||48||+||55||103||chr1||48||+||48||96||2
        48 0 0
        0
        """)
    )
    return build_filesystem_test_repository(root_path)


@pytest.mark.parametrize("spos, expected", [
    (("1", 5), ("chr1", 1, "+", 4900)),
    (("1", 14), ("chr1", 10, "+", 4900)),
    (("1", 56), ("chr1", 48, "+", 4900)),
    (("1", 80), ("chr1", 72, "+", 4900)),
    (("1", 53), None),
    (("2", 56), None),
])
def test_liftover_chain_fixture(
        spos: tuple[str, int],
        expected: Optional[tuple[str, int, str, int]],
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
    (Region("1", 5, 53), None),
    (Region("1", 5, 56), Region("chr1", 1, 48)),
    (CNVAllele("1", 5, 56, CNVAllele.Type.LARGE_DELETION),
     CNVAllele("chr1", 1, 48, CNVAllele.Type.LARGE_DELETION))
])
def test_liftover_annotator(
        annotatable: Annotatable,
        expected: Optional[Annotatable],
        fixture_repo: GenomicResourceRepo) -> None:

    pipeline_config = textwrap.dedent("""
        - liftover_annotator:
            target_genome: target_genome
            chain: liftover_chain
            attributes:
            - source: liftover_annotatable
              internal: false
    """)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=fixture_repo)

    with pipeline.open() as work_pipeline:
        result = work_pipeline.annotate(annotatable)
        print(annotatable, result)

    print(annotatable, result)
    assert result["liftover_annotatable"] == expected
