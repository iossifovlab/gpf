# pylint: disable=redefined-outer-name,C0114,C0116,protected-access,fixme

import textwrap

import pytest
from dae.annotation.annotatable import (
    Annotatable,
    CNVAllele,
    Region,
)
from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.genomic_resources.repository import GenomicResourceProtocolRepo
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
)
from dae.testing.t4c8_import import (
    t4c8_genes,
    t4c8_genome,
)


@pytest.fixture
def fixture_repo(
    tmp_path_factory: pytest.TempPathFactory,
) -> GenomicResourceProtocolRepo:
    root_path = tmp_path_factory.mktemp(__name__)
    t4c8_genome(root_path)
    t4c8_genes(root_path)
    return build_filesystem_test_repository(root_path)


@pytest.mark.parametrize(
    "annotatable, worst_effect, gene_effects, effect_details, gene_list", [
        (Region("chr1", 1, 19),
         "unknown", "t4:unknown", "tx1:t4:unknown:19", {"t4"}),
        (CNVAllele("chr1", 1, 29, Annotatable.Type.LARGE_DELETION),
         "CNV-", "t4:CNV-", "tx1:t4:CNV-:29", {"t4"}),
        (CNVAllele("chr1", 1, 29, Annotatable.Type.LARGE_DUPLICATION),
         "CNV+", "t4:CNV+", "tx1:t4:CNV+:29", {"t4"}),
        (CNVAllele("chr1", 93, 95, Annotatable.Type.LARGE_DUPLICATION),
         "CNV+", "intergenic:CNV+", "intergenic:intergenic:CNV+:3",
         set()),
        (Region("chr1", 93, 95),
         "unknown", "intergenic:unknown", "intergenic:intergenic:unknown:3",
         set()),
        (CNVAllele("chr1", 1, 150, Annotatable.Type.LARGE_DUPLICATION),
         "CNV+", "t4:CNV+|c8:CNV+", "tx1:t4:CNV+:150|tx1:c8:CNV+:150",
         {"t4", "c8"}),
    ],
)
def test_effect_annotator(
    annotatable: Annotatable,
    worst_effect: str,
    gene_effects: str,
    effect_details: str,
    gene_list: set[str],
    fixture_repo: GenomicResourceProtocolRepo,
) -> None:

    pipeline_config = textwrap.dedent("""
        - effect_annotator:
            genome: t4c8_genome
            gene_models: t4c8_genes
    """)

    pipeline = load_pipeline_from_yaml(pipeline_config, fixture_repo)

    result = None
    with pipeline.open() as work_pipeline:
        result = work_pipeline.annotate(annotatable)
        print(annotatable, result)

    print(annotatable, result)
    assert result is not None
    assert result["worst_effect"] == worst_effect
    assert result["gene_effects"] == gene_effects
    assert result["effect_details"] == effect_details
    assert set(result["gene_list"]) == gene_list
