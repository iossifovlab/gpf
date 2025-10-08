# pylint: disable=W0621,C0114,C0116,W0212,W0613

import os
import pathlib
import textwrap
from collections.abc import Generator
from typing import Any

import pytest
from dae.annotation.annotatable import Annotatable
from dae.annotation.annotation_config import AnnotatorInfo, AttributeInfo
from dae.annotation.annotation_pipeline import Annotator
from dae.genomic_resources.genomic_context import (
    _REGISTERED_CONTEXTS,
)
from dae.genomic_resources.testing import (
    setup_denovo,
    setup_directories,
    setup_genome,
)


class DummyAnnotator(Annotator):
    """A dummy annotator that does nothing."""

    def __init__(
        self,
        attributes: list[AttributeInfo] | None = None,
        dependencies: tuple[str, ...] = (),
    ) -> None:
        self.dependencies = dependencies

        info = AnnotatorInfo(
            "dummy_annotator",
            annotator_id="dummy",
            attributes=attributes or [],
            parameters={},
        )
        super().__init__(None, info)
        self.index = 0

    @property
    def used_context_attributes(self) -> tuple[str, ...]:
        return self.dependencies

    def open(self) -> Annotator:
        """Reset the annotator state."""
        self.index = 0
        return self

    def annotate(
        self, annotatable: Annotatable | None,
        context: dict[str, Any],  # noqa: ARG002
    ) -> dict[str, Any]:
        """Produce annotation attributes for an annotatable."""
        if annotatable is None:
            return {}
        self.index += 1
        return {"index": self.index, "annotatable": annotatable}


def relative_to_this_test_folder(path: str) -> str:
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


@pytest.fixture
def clear_context() -> Generator[None, None, None]:
    # No setup
    yield
    # Teardown - clear genomic contexts
    _REGISTERED_CONTEXTS.clear()


@pytest.fixture(scope="session")
def work_dir() -> str:
    return relative_to_this_test_folder("fixtures")


@pytest.fixture(scope="module")
def annotate_directory_fixture(
    tmp_path_factory: pytest.TempPathFactory,
) -> pathlib.Path:
    root_path = tmp_path_factory.mktemp("annotate_tests_fixtures")
    setup_directories(
        root_path,
        {
            "annotation.yaml": """
                - position_score: one
            """,
            "annotation_duplicate.yaml": """
                - position_score: one
                - position_score: one
            """,
            "annotation_multiallelic.yaml": """
                - allele_score: two
            """,
            "annotation_forbidden_symbols.yaml": """
                - allele_score: three
            """,
            "annotation_quotes_in_description.yaml": """
                - position_score: four
            """,
            "annotation_repeated_attributes.yaml": """
                - position_score: one
                - position_score: four
            """,
            "annotation_internal_attributes.yaml": """
                - position_score:
                    resource_id: one
                    attributes:
                    - source: score
                      name: score_1
                - position_score:
                    resource_id: four
                    attributes:
                    - source: score
                      name: score_4
                      internal: true
            """,
            "grr.yaml": f"""
                id: mm
                type: dir
                directory: "{root_path}/grr"
            """,
            "grr": {
                "one": {
                    "genomic_resource.yaml": """
                        type: position_score
                        table:
                            filename: data.txt
                        scores:
                        - id: score
                          type: float
                          desc: |
                                The phastCons computed over the tree of 100
                                verterbrate species
                          name: s1
                    """,
                },
                "two": {
                    "genomic_resource.yaml": """
                        type: allele_score
                        table:
                            filename: data.txt
                            reference:
                              name: reference
                            alternative:
                              name: alternative
                        scores:
                        - id: score
                          type: float
                          name: s1
                    """,
                },
                "three": {
                    "genomic_resource.yaml": """
                        type: allele_score
                        table:
                            filename: data.txt
                            reference:
                              name: reference
                            alternative:
                              name: alternative
                        scores:
                        - id: score
                          type: str
                          name: s1
                    """,
                },
                "four": {
                    "genomic_resource.yaml": """
                        type: position_score
                        table:
                            filename: data.txt
                        scores:
                        - id: score
                          type: float
                          desc: |
                                The "phastCons" computed over the tree of 100
                                verterbrate species
                          name: s1
                    """,
                },
                "res_pipeline": {
                    "annotation.yaml": """
                        - position_score: one
                    """,
                    "genomic_resource.yaml": """
                        type: annotation_pipeline
                        filename: annotation.yaml
                    """,
                },
                "test_genome": {
                    "genomic_resource.yaml": """
                        type: genome
                        filename: genome.fa
                    """,
                },
            },
        },
    )
    one_content = textwrap.dedent("""
        chrom  pos_begin  s1
        chr1   23         0.1
        chr1   24         0.2
        chr2   33         0.3
        chr2   34         0.4
        chr3   43         0.5
        chr3   44         0.6
        chr4   53         0.1234567890123456789
    """)
    two_content = textwrap.dedent("""
        chrom  pos_begin  reference  alternative  s1
        chr1   23         C          T            0.1
        chr1   23         C          A            0.2
        chr1   24         C          A            0.3
        chr1   24         C          G            0.4
        chr1   25         C          G            0.4
    """)
    three_content = textwrap.dedent("""
        chrom  pos_begin  reference  alternative  s1
        chr1   23         C          A            a;b
        chr1   24         C          A            c,d
        chr1   25         C          A            e||f
    """)
    four_content = textwrap.dedent("""
        chrom  pos_begin  s1
        chr1   23         0.101
        chr1   24         0.201
        chr2   33         0.301
        chr2   34         0.401
        chr3   43         0.501
        chr3   44         0.601
    """)

    setup_denovo(root_path / "grr" / "one" / "data.txt", one_content)
    setup_denovo(root_path / "grr" / "two" / "data.txt", two_content)
    setup_denovo(root_path / "grr" / "three" / "data.txt", three_content)
    setup_denovo(root_path / "grr" / "four" / "data.txt", four_content)

    setup_genome(
        root_path / "grr" / "test_genome" / "genome.fa",
        textwrap.dedent(f"""
        >chr1
        {25 * 'ACGT'}
        >chr2
        {25 * 'ACGT'}
        >chr3
        {25 * 'ACGT'}
        >chr4
        {25 * 'ACGT'}
        """))

    return root_path
