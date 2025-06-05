# pylint: disable=redefined-outer-name,C0114,C0116,protected-access,fixme

import textwrap

import pytest

from dae.annotation.annotatable import Annotatable, CNVAllele, Position, Region
from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    setup_directories,
    setup_genome,
)


@pytest.fixture()
def fixture_repo(
    tmp_path_factory: pytest.TempPathFactory,
) -> GenomicResourceRepo:
    root_path = tmp_path_factory.mktemp("regions_effect_annotation")
    setup_directories(root_path, {
        "genome": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: genome
                filename: genome.fa
            """),
        },
    })
    setup_genome(
        root_path / "genome" / "genome.fa",
        textwrap.dedent(f"""
            >chr1
            {25 * 'AGCT'}
            >chr2
            {25 * 'AGCT'}
            """),
    )
    return build_filesystem_test_repository(root_path)


@pytest.mark.parametrize("annotatable, expected", [
    (Position("chr1", 1), Position("chr1", 1)),
    (Region("chr1", 1, 10), Region("chr1", 1, 10)),
    (CNVAllele("chr1", 1, 10, CNVAllele.Type.LARGE_DELETION),
     CNVAllele("chr1", 1, 10, CNVAllele.Type.LARGE_DELETION)),
])
def test_normalize_allele_annotator(
    annotatable: Annotatable,
    expected: Annotatable,
    fixture_repo: GenomicResourceRepo,
) -> None:
    pipeline_config = textwrap.dedent("""
        - normalize_allele_annotator:
            genome: genome
            attributes:
            - source: normalized_allele
              name: normalized_allele
              internal: False
    """)

    pipeline = load_pipeline_from_yaml(pipeline_config, fixture_repo)

    with pipeline.open() as work_pipeline:
        result = work_pipeline.annotate(annotatable)
        print(annotatable, result)

    print(annotatable, result)
    assert result["normalized_allele"] == expected
