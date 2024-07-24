# pylint: disable=W0621,C0114,C0116,W0212,W0613
import shutil
import tempfile
import textwrap
from collections.abc import Generator
from io import StringIO
from pathlib import Path
from typing import Any, cast

import pytest
from pytest_mock import MockerFixture

from dae.annotation.annotatable import Annotatable, VCFAllele
from dae.annotation.annotation_factory import load_pipeline_from_yaml
from vep_annotator.vep_annotator import VEPCacheAnnotator


@pytest.fixture()
def vep_annotator(
    mocker: MockerFixture,
    vep_fixtures: Path,
) -> Generator[VEPCacheAnnotator, None, None]:

    temp_cache_dir = tempfile.mkdtemp(prefix="vep_cache_test")

    pipeline = load_pipeline_from_yaml(textwrap.dedent(f"""
        - vep_full_annotator:
            cache_dir: {temp_cache_dir}
            work_dir: {vep_fixtures}
            attributes:
              - name: vep_gene
                source: gene
              - name: feature
              - name: feature_type
              - name: consequence
              - name: gene_id
              - name: location
              - name: allele
              - name: cdna_position
              - name: cds_position
              - name: protein_position
              - name: amino_acids
              - name: codons
              - name: existing_variation
              - name: impact
              - name: distance
              - name: strand
              - name: symbol_source
              - name: worst_consequence
              - name: highest_impact
              - name: gene_consequence
    """), None)  # type: ignore
    annotator = pipeline.annotators[0]

    annotator.work_dir = Path(annotator.work_dir)  # type: ignore

    mocker.patch.object(
        annotator,
        "run_vep",
        return_value=None,
    )
    mocker.patch.object(
        annotator,
        "open_files",
        return_value=(
            (vep_fixtures / "input.tsv").open("r"),
            (vep_fixtures / "output.tsv").open("r"),
        ),
    )

    yield cast(VEPCacheAnnotator, annotator)

    shutil.rmtree(temp_cache_dir)


def test_prepare_input(vep_annotator: VEPCacheAnnotator) -> None:
    annotatables: list[VCFAllele | None] = [
        VCFAllele("1", 10, "A", "C"),
        VCFAllele("1", 11, "ACG", "A"),
        VCFAllele("1", 15, "A", "CGT"),
        VCFAllele("1", 20, "A", "ATGAC"),
    ]
    file = StringIO()
    vep_annotator.prepare_input(file, annotatables)
    file.seek(0)

    line = file.readline()
    cols = line.strip().split("\t")
    assert len(cols) == 6
    assert cols[0] == "1"
    assert cols[1] == "10"
    assert cols[2] == "10"
    assert cols[3] == "A/C"
    assert cols[4] == "+"
    assert cols[5] == "1"

    line = file.readline()
    cols = line.strip().split("\t")
    assert len(cols) == 6
    assert cols[0] == "1"
    assert cols[1] == "12"
    assert cols[2] == "13"
    assert cols[3] == "CG/-"
    assert cols[4] == "+"
    assert cols[5] == "2"

    line = file.readline()
    cols = line.strip().split("\t")
    assert len(cols) == 6
    assert cols[0] == "1"
    assert cols[1] == "15"
    assert cols[2] == "16"
    assert cols[3] == "A/CGT"
    assert cols[4] == "+"
    assert cols[5] == "3"

    line = file.readline()
    cols = line.strip().split("\t")
    assert len(cols) == 6
    assert cols[0] == "1"
    assert cols[1] == "21"
    assert cols[2] == "20"
    assert cols[3] == "-/TGAC"
    assert cols[4] == "+"
    assert cols[5] == "4"


def test_aggregate_attributes(vep_annotator: VEPCacheAnnotator) -> None:
    contexts: list[dict[str, Any]] = [{
        "sample1": ["1", "2", "3"],
        "sample2": ["4", "5", "6"],
    }]

    vep_annotator.aggregate_attributes(contexts, ["sample1", "sample2"])
    assert contexts[0]["sample1"] == "1;2;3"
    assert contexts[0]["sample2"] == "4;5;6"


def test_read_output(
    vep_annotator: VEPCacheAnnotator, vep_fixtures: Path,
) -> None:
    output_file = (vep_fixtures / "output.tsv").open("r")
    contexts: list[dict[str, Any]] = [
        {},
        {},
        {},
        {},
    ]

    vep_annotator.read_output(output_file, contexts)

    assert len(contexts[0]) == 20
    assert contexts[0]["worst_consequence"] == ["splice_acceptor_variant"]
    assert contexts[0]["highest_impact"] == ["HIGH"]

    assert len(contexts[1]) == 20
    assert contexts[1]["worst_consequence"] == ["stop_gained"]
    assert contexts[1]["highest_impact"] == ["HIGH"]

    assert len(contexts[2]) == 20
    assert contexts[2]["worst_consequence"] == ["frameshift_variant"]
    assert contexts[2]["highest_impact"] == ["HIGH"]

    assert len(contexts[3]) == 20
    assert contexts[3]["worst_consequence"] == ["stop_gained"]
    assert contexts[3]["highest_impact"] == ["HIGH"]


def test_mock_annotate(
    vep_annotator: VEPCacheAnnotator,
    mocker: MockerFixture,
    vep_fixtures: Path,
) -> None:
    mocker.patch.object(
        vep_annotator,
        "run_vep",
        return_value=None,
    )
    mocker.patch.object(
        vep_annotator,
        "prepare_input",
        return_value=None,
    )
    mocker.patch.object(
        vep_annotator,
        "open_files",
        return_value=(
            (vep_fixtures / "input.tsv").open("r"),
            (vep_fixtures / "output.tsv").open("r"),
        ),
    )
    annotatables: list[Annotatable | None] = [
        VCFAllele("1", 10, "A", "C"),
        VCFAllele("1", 11, "ACG", "A"),
        VCFAllele("1", 15, "A", "CGT"),
        VCFAllele("1", 20, "A", "ATGAC"),
    ]
    contexts: list[dict[str, Any]] = [{}, {}, {}, {}]

    vep_annotator.batch_annotate(annotatables, contexts)

    assert len(contexts[0]) == 20
    assert contexts[0]["worst_consequence"] == "splice_acceptor_variant"
    assert contexts[0]["highest_impact"] == "HIGH"

    assert len(contexts[1]) == 20
    assert contexts[1]["worst_consequence"] == "stop_gained"
    assert contexts[1]["highest_impact"] == "HIGH"

    assert len(contexts[2]) == 20
    assert contexts[2]["worst_consequence"] == "frameshift_variant"
    assert contexts[2]["highest_impact"] == "HIGH"

    assert len(contexts[3]) == 20
    assert contexts[3]["worst_consequence"] == "stop_gained"
    assert contexts[3]["highest_impact"] == "HIGH"
