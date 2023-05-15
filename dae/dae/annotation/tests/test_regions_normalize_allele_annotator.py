# pylint: disable=redefined-outer-name,C0114,C0116,protected-access,fixme

import textwrap
import pytest

from dae.genomic_resources.testing import \
    setup_directories, setup_genome, \
    build_filesystem_test_repository

from dae.annotation.annotatable import Region, Position, CNVAllele
from dae.annotation.annotation_factory import build_annotation_pipeline


@pytest.fixture
def fixture_repo(tmp_path_factory):
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
            """)
    )
    return build_filesystem_test_repository(root_path)


@pytest.mark.parametrize("annotatable, expected", [
    (Position("chr1", 1), Position("chr1", 1)),
    (Region("chr1", 1, 10), Region("chr1", 1, 10)),
    (CNVAllele("chr1", 1, 10, CNVAllele.Type.LARGE_DELETION),
     CNVAllele("chr1", 1, 10, CNVAllele.Type.LARGE_DELETION))
])
def test_normalize_allele_annotator(
        annotatable, expected, fixture_repo):

    pipeline_config = textwrap.dedent("""
        - normalize_allele_annotator:
            genome: genome
            attributes:
            - source: normalized_allele
              dest: normalized_allele
              internal: False
    """)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=fixture_repo)

    with pipeline.open() as work_pipeline:
        result = work_pipeline.annotate(annotatable)
        print(annotatable, result)

    print(annotatable, result)
    assert result["normalized_allele"] == expected
