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


class DemoAnnotateGeneModelsAdapter(AnnotatorBase):
    """Annotation pipeline adapter for dummy_annotate using tempfiles."""

    def __init__(
        self, pipeline: Optional[AnnotationPipeline],
        info: AnnotatorInfo,
    ):
        if not info.attributes:
            info.attributes = AnnotationConfigParser.parse_raw_attributes([
                "gene_symbols",
            ])
        self.work_dir: Path = info.parameters.get("work_dir")
        self.cache_repo = GenomicResourceCachedRepo(
            pipeline.repository, self.work_dir / "grr_cache",
        )
        gene_models_id = info.parameters.get("gene_models")
        self.gene_models_resource = self.cache_repo.get_resource(gene_models_id)

        self.gene_model_filename = \
            self.gene_models_resource.get_config()["filename"]
        self.gene_model_format = \
            self.gene_models_resource.get_config()["format"]

        super().__init__(
            pipeline, info, {
                "gene_symbols": ("object", "Gene symbols overlapping"
                                           "with the annotatable"),
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
            contexts[idx]["gene_symbols"] = row[-1]

    def batch_annotate(
        self, annotatables: list[Optional[Annotatable]],
        contexts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        print("Getting filepath")
        print(self.gene_model_filename)
        print(self.gene_models_resource.get_file_url(self.gene_model_filename))
        gene_model_filepath = fsspec.url_to_fs(
            self.gene_models_resource.get_file_url(self.gene_model_filename),
        )[1]
        print(f"Done - {gene_model_filepath}")

        with (self.work_dir / "input.tsv").open("w+t") as input_file, \
                (self.work_dir / "output.tsv").open("w+t") as out_file:
            self.prepare_input(input_file, annotatables)
            args = [
                "demo_annotate_gm_res", input_file.name,
                gene_model_filepath, out_file.name,
            ]
            if self.gene_model_format:
                args += ["--format", self.gene_model_format]
            print(args)
            subprocess.run(args, check=True)
            out_file.flush()
            self.read_output(out_file, contexts)
        return contexts


def build_demo_external_gene_annotator_adapter(
    pipeline: AnnotationPipeline,
    info: AnnotatorInfo,
) -> Annotator:
    return DemoAnnotateGeneModelsAdapter(pipeline, info)
