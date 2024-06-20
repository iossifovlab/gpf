from __future__ import annotations

import csv
import subprocess
from pathlib import Path
from typing import Any, Optional, TextIO

import fsspec

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotation_factory import AnnotationConfigParser
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    Annotator,
    AnnotatorInfo,
)
from dae.annotation.annotator_base import AnnotatorBase
from dae.genomic_resources.cached_repository import GenomicResourceCachedRepo

# ruff: noqa: S607


class DemoAnnotateGenomeAdapter(AnnotatorBase):
    """Annotation pipeline adapter for dummy_annotate using tempfiles."""

    def __init__(
        self, pipeline: Optional[AnnotationPipeline],
        info: AnnotatorInfo,
    ):
        if not info.attributes:
            info.attributes = AnnotationConfigParser.parse_raw_attributes([
                "ref_sequence",
            ])
        self.work_dir: Path = info.parameters.get("work_dir")
        self.cache_repo = GenomicResourceCachedRepo(
            pipeline.repository, self.work_dir / "grr_cache",
        )
        genome_id = info.parameters.get("reference_genome")
        self.genome_resource = self.cache_repo.get_resource(genome_id)

        self.genome_filename = \
            self.genome_resource.get_config()["filename"]

        super().__init__(
            pipeline, info, {
                "ref_sequence": ("object", "Sequence in the reference"
                                           "genome"),
            },
        )

    def _do_annotate(
        self, _annotatable: Optional[Annotatable],
        _context: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError(
            "External annotator supports only batch mode",
        )

    def annotate(
        self, _annotatable: Optional[Annotatable],
        _context: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError(
            "External annotator supports only batch mode",
        )

    def prepare_input(
        self, file: TextIO, annotatables: list[Optional[Annotatable]],
    ) -> None:
        writer = csv.writer(file, delimiter="\t")
        for annotatable in annotatables:
            writer.writerow([repr(annotatable)])
        file.flush()

    def read_output(
        self, file: TextIO, contexts: list[dict[str, Any]],
    ) -> None:
        """Read and return subprocess output contents."""
        reader = csv.reader(
            file, delimiter="\t",
        )
        for idx, row in enumerate(reader):
            contexts[idx]["ref_sequence"] = row[-1]

    def batch_annotate(
        self, annotatables: list[Optional[Annotatable]],
        contexts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        genome_filepath = fsspec.url_to_fs(
            self.genome_resource.get_file_url(self.genome_filename),
        )[1]
        self.genome_resource.get_file_url(f"{self.genome_filename}.fai")

        with (self.work_dir / "input.tsv").open("w+t") as input_file, \
                (self.work_dir / "output.tsv").open("w+t") as out_file:
            self.prepare_input(input_file, annotatables)
            args = [
                "demo_annotate_ref_res", input_file.name,
                genome_filepath, out_file.name,
            ]
            subprocess.run(args, check=True)
            out_file.flush()
            self.read_output(out_file, contexts)
        return contexts


def build_demo_external_genome_annotator_adapter(
    pipeline: AnnotationPipeline,
    info: AnnotatorInfo,
) -> Annotator:
    return DemoAnnotateGenomeAdapter(pipeline, info)
