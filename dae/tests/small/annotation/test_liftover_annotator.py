# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

import pytest
from dae.annotation.annotation_factory import (
    load_pipeline_from_yaml,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    setup_directories,
)


@pytest.fixture
def dummy_liftover_grr_fixture(
    tmp_path_factory: pytest.TempPathFactory,
) -> GenomicResourceRepo:
    root_path = tmp_path_factory.mktemp("dummy_liftover_grr_fixture")
    setup_directories(root_path, {
        "genomeA": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: genome
                filename: genome.fa
            """),
        },
        "genomeB": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: genome
                filename: genome.fa
            """),
        },
        "dummyChain": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: liftover_chain
                filename: liftover.chain.gz
                meta:
                  labels:
                    source_genome: genomeA
                    target_genome: genomeB
            """),
        },
    })
    return build_filesystem_test_repository(root_path)


def test_liftover_annotator_implicit_genomes(
    dummy_liftover_grr_fixture: GenomicResourceRepo,
) -> None:
    pipeline_config = textwrap.dedent("""
      - liftover_annotator:
          chain: dummyChain
      """)
    pipeline = load_pipeline_from_yaml(
        pipeline_config, dummy_liftover_grr_fixture)
    assert pipeline.get_resource_ids() == {
        "genomeA",
        "genomeB",
        "dummyChain",
    }
