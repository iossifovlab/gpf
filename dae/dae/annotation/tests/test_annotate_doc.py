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
                - preambule:
                    reference_genome: acgt
                    description: sample description
                    metadata:
                        a: b
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
    assert pathlib.Path(output_file).read_text() == f"""<html>

<head>
    <style>
        h3,
        h4 {{
            margin-top: 0.5em;
            margin-bottom: 0.5em;
        }}

        .annotator_line {{
            font-size: 14px;
            background-color: aquamarine;
            vertical-align: top;
        }}

        .attribute_description {{
            font-size: 14px;
        }}

        .attribute_name {{
            font-size: 20px;
        }}

        .resource {{
            background-color: rgb(233, 151, 151);
        }}
    </style>
</head>

<body>
    <h1>Pipeline Documentation</h1>
    <h3>Preambule</h3>
    <ul>
        <li>Reference genome: acgt</li>
        <li>Description: sample description</li>
        <li>
            Metadata:
            <ul>
                <li>a = b</li>
            </ul>
        </li>
    </ul>
    <table border="1">
        <tr>
            <th>Attribute</th>
            <th>Type</th>
            <th>Description</th>
        </tr>
        <tr class="annotator_line">
            <td>
                <p><b>Annotator</b></p>
                <p>type: position_score</p>
                <p>description: <ul>
<li><p>Annotator to use with genomic scores depending on genomic position like
phastCons, phyloP, FitCons2, etc.</p></li>
<li><p><a href="https://www.iossifovlab.com/gpfuserdocs/administration/annotation_tools.html#position-score" target="_blank">More info</a></p></li>
</ul>
</p>
            </td>
            <td colspan="2">
                <table border="3">
                    <tr>
                        <td class="resource">
                            <p><b>Resource</b></p>
                            <p>id: <a href="file://{tmp_path}/one/index.html">
                                    one</a></p>                            
                            <p>type: position_score</p>
                            <p>description: <p></p>
</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr class="attribute">
            <td>
                <div>
                    <p class="attribute_name">score_one</p>
                </div>
            </td>
            <td>
                <div class="attribute">
                    <p>float</p>
                </div>
            </td>
            <td>
                <div class="attribute_description">
                    <p>source: score_one</p>
                    <p><img src="file://{tmp_path}/one/statistics/histogram_score_one.png" alt="HISTOGRAM" /></p>

<p>small values: None,
large_values None</p>

<p><strong>position_aggregator</strong>: <code>mean</code> [default]</p>

                </div>
            </td>
        </tr>
    </table>
    <html>
</body>"""
