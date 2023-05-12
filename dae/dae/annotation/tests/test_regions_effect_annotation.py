# pylint: disable=redefined-outer-name,C0114,C0116,protected-access,fixme

import textwrap
import pytest

from dae.genomic_resources.testing import \
    setup_directories, convert_to_tab_separated, setup_genome, \
    build_filesystem_test_repository
from dae.annotation.annotatable import Region, Position
from dae.annotation.annotation_factory import build_annotation_pipeline


@pytest.fixture
def fixture_repo(tmp_path_factory):
    root_path = tmp_path_factory.mktemp("regions_effect_annotation")
    setup_directories(root_path, {
        "gene_models": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: gene_models
                filename: gene_models.tsv
                format: "refflat"
            """),

            "gene_models.tsv": convert_to_tab_separated("""
                #geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds 
                g1        tx1  chr1  +      3       17    3        17     2         3,13       6,17
                g1        tx2  chr1  +      3       9     3        6      1         3          6
                g2        tx3  chr1  -      20      39    23       35     1         23         35
                """)  # noqa

        },
        "genome": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: genome
                filename: genome.fa
            """),
        }
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
    (Region("chr1", 1, 19), ["g1"]),
    (Region("chr1", 1, 29), ["g1", "g2"]),
    (Position("chr1", 10), ["g1"]),
])
def test_effect_annotator(
        annotatable, expected, fixture_repo):

    pipeline_config = textwrap.dedent("""
        - effect_annotator:
            genome: genome
            gene_models: gene_models
    """)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=fixture_repo)

    with pipeline.open() as work_pipeline:
        result = work_pipeline.annotate(annotatable)
        print(annotatable, result)

    print(annotatable, result)
    assert sorted(result["gene_list"]) == expected
