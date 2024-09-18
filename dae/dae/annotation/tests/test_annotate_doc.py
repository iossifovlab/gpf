# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap
from typing import Callable

import pytest

from dae.annotation.annotate_doc import cli
from dae.genomic_resources.genomic_context import GenomicContext
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.testing import (
    setup_denovo,
    setup_directories,
)
from dae.testing.t4c8_import import t4c8_gpf


@pytest.fixture()
def t4c8_instance(tmp_path: pathlib.Path) -> GPFInstance:
    root_path = tmp_path
    setup_directories(
        root_path,
        {
            "grr.yaml": textwrap.dedent(f"""
                id: t4c8_local
                type: directory
                directory: {root_path!s}
            """),
            "pipeline_config.yaml": textwrap.dedent("""
                preamble:
                    input_reference_genome: acgt
                    summary: asdf summary
                    description: sample description
                    metadata:
                        a: b
                annotators:
                    - position_score: one
            """),
            "one": {
                "genomic_resource.yaml": textwrap.dedent("""
                        type: position_score
                        table:
                            filename: data.txt
                        scores:
                        - id: score_one
                          type: float
                          name: score
                """),
            },
            "acgt": {
                "genomic_resource.yaml": textwrap.dedent("""
                    type: reference_genome
                    filename: genome.fa
                """),
                "genome.fa": """blabla""",
            },
        },
    )
    one_content = textwrap.dedent("""
        chrom  pos_begin  score
        chr1   4          0.01
    """)
    setup_denovo(root_path / "one" / "data.txt", one_content)
    return t4c8_gpf(root_path)


def test_annotate_doc(
    tmp_path: pathlib.Path,
    t4c8_instance: GPFInstance,
    gpf_instance_genomic_context_fixture: Callable[[GPFInstance], GenomicContext],  # noqa: E501
) -> None:
    root_path = pathlib.Path(t4c8_instance.dae_dir) / ".."
    pipeline_config = str(root_path / "pipeline_config.yaml")
    output_file = tmp_path / "output.html"

    gpf_instance_genomic_context_fixture(t4c8_instance)

    cli([
        pipeline_config,
        "-o", str(output_file),
    ])

    output_template = pathlib.Path(output_file).read_text()

    assert f"""src=\"file://{tmp_path}/one/statistics/histogram_score_one.png\"""" in output_template  # noqa: E501
    assert "<strong>position_aggregator</strong>" in output_template
    assert f"""href=\"file://{tmp_path}/one/index.html\"""" in output_template
    assert 'href="https://www.iossifovlab.com/gpfuserdocs/administration/annotation.html#position-score"' in output_template  # noqa: E501
    assert "Annotator to use with genomic scores depending on genomic position" in output_template  # noqa: E501

    assert "preamble" in output_template
    assert "acgt" in output_template
    assert "asdf summary" in output_template
    assert "sample description" in output_template
    assert f'<a href="file://{tmp_path}/acgt/index.html">' in output_template
