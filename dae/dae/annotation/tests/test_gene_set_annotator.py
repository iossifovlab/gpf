# pylint: disable=W0621,C0114,C0116,W0212,W0613

import textwrap
import pytest

from dae.annotation.annotation_pipeline import AnnotatorInfo
from dae.annotation.gene_set_annotator import GeneSetAnnotator
from dae.testing import setup_directories
from dae.genomic_resources.repository_factory import \
    build_genomic_resource_repository
from dae.genomic_resources.repository import GenomicResourceRepo


@pytest.fixture(scope="module")
def test_grr(tmp_path_factory: pytest.TempPathFactory) -> GenomicResourceRepo:
    root_path = tmp_path_factory.mktemp("test_grr")
    setup_directories(
        root_path, {
            "grr.yaml": textwrap.dedent(f"""
                id: reannotation_repo
                type: dir
                directory: "{root_path}/grr"
            """),
            "grr": {
                "foobar_gene_set_collection": {
                    "genomic_resource.yaml": textwrap.dedent("""
                        id: pesho
                        type: gene_set
                        format: directory
                        directory: geneSets
                    """),
                    "geneSets": {
                        "set_1.txt": textwrap.dedent("""set_1
                            random test gene set description
                            g1
                            g2
                        """)
                    }
                }
            }
        }
    )
    return build_genomic_resource_repository(file_name=str(
        root_path / "grr.yaml"
    ))


def test_gene_set_annotator(test_grr: GenomicResourceRepo) -> None:
    resource = test_grr.get_resource("foobar_gene_set_collection")
    annotator = GeneSetAnnotator(
        None, AnnotatorInfo("gosho", [], {}), resource, "set_1", "gene_list"
    )

    result = annotator.annotate(None, {"gene_list": ["g1"]})
    assert result == {"in_set_1": True}

    result = annotator.annotate(None, {"gene_list": ["g3"]})
    assert result == {"in_set_1": False}

    result = annotator.annotate(None, {"gene_list": ["g3", "g2"]})
    assert result == {"in_set_1": True}


def test_gene_score_annotator_used_context_attributes(
    test_grr: GenomicResourceRepo
) -> None:
    resource = test_grr.get_resource("foobar_gene_set_collection")
    annotator = GeneSetAnnotator(
        None, AnnotatorInfo("gosho", [], {}), resource, "set_1", "gene_list"
    )

    assert annotator.used_context_attributes == ("gene_list",)
