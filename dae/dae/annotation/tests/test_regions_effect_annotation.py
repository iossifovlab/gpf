# pylint: disable=redefined-outer-name,C0114,C0116,protected-access,fixme

import textwrap

import pytest

from dae.annotation.annotatable import Annotatable, CNVAllele, Position, Region
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.genomic_resources.repository import GenomicResourceProtocolRepo
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    convert_to_tab_separated,
    setup_directories,
    setup_genome,
)


@pytest.fixture()
def fixture_repo(
    tmp_path_factory: pytest.TempPathFactory,
) -> GenomicResourceProtocolRepo:
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


@pytest.mark.parametrize(
    "annotatable, gene_list, effect_type, length, txs", [
        (Region("chr1", 1, 19), ["g1"], "unknown", 19,
         {"g1": ["tx1", "tx2"]}),
        (Region("chr1", 1, 29), ["g1", "g2"], "unknown", 29,
         {"g1": ["tx1", "tx2"], "g2": ["tx3"]}),
        (Position("chr1", 10), ["g1"], "unknown", 1,
         {"g1": ["tx1"]}),
        (CNVAllele("chr1", 1, 29, Annotatable.Type.LARGE_DELETION),
         ["g1", "g2"], "CNV-", 29,
         {"g1": ["tx1", "tx2"], "g2": ["tx3"]}),
        (CNVAllele("chr1", 1, 29, Annotatable.Type.LARGE_DUPLICATION),
         ["g1", "g2"], "CNV+", 29,
         {"g1": ["tx1", "tx2"], "g2": ["tx3"]}),
    ],
)
def test_effect_annotator(
        annotatable: Annotatable,
        gene_list: list[str],
        effect_type: str, length: int,
        txs: dict[str, list[str]],
        fixture_repo: GenomicResourceProtocolRepo,
) -> None:

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
    assert sorted(result["gene_list"]) == gene_list
    assert result["worst_effect"] == effect_type
    assert result["gene_effects"] == "|".join([
        f"{g}:{effect_type}" for g in gene_list])
    assert result["effect_details"] == "|".join([
        f"{t}:{g}:{effect_type}:{length}"
        for g, ts in txs.items()
        for t in ts
    ])


@pytest.mark.parametrize("annotatable, effect_type, length", [
    (Region("chr1", 1, 19), "unknown", 19),
    (CNVAllele("chr1", 1, 29, Annotatable.Type.LARGE_DELETION),
     "CNV-", 29),
    (CNVAllele("chr1", 1, 29, Annotatable.Type.LARGE_DUPLICATION),
     "CNV+", 29),
])
def test_effect_annotator_region_length_cutoff(
    annotatable: Annotatable,
    effect_type: str,
    length: int,
    fixture_repo: GenomicResourceProtocolRepo,
) -> None:

    pipeline_config = textwrap.dedent("""
        - effect_annotator:
            genome: genome
            gene_models: gene_models
            region_length_cutoff: 5
    """)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=fixture_repo)

    with pipeline.open() as work_pipeline:
        result = work_pipeline.annotate(annotatable)
        print(annotatable, result)

    print(annotatable, result)
    assert result["worst_effect"] == effect_type
    assert result["gene_effects"] == f"None:{effect_type}"
    assert result["effect_details"] == f"None:None:{effect_type}:{length}"
    assert result.get("gene_list") == []
