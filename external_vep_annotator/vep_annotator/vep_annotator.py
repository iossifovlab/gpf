from __future__ import annotations

import copy
import csv
import os
import subprocess
from pathlib import Path
from typing import Any, TextIO, cast

import fsspec

from dae.annotation.annotatable import Annotatable, VCFAllele
from dae.annotation.annotation_factory import AnnotationConfigParser
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    Annotator,
    AnnotatorInfo,
)
from dae.annotation.annotator_base import AnnotatorBase
from dae.genomic_resources.cached_repository import GenomicResourceCachedRepo
from dae.genomic_resources.gene_models import (
    build_gene_models_from_resource,
    gene_models_to_gtf,
)
from vep_annotator.vep_attributes import effect_attributes, full_attributes

# ruff: noqa: S607

CONSEQUENCES: dict[str, int] = {t[1]: t[0] for t in enumerate([
    "sequence_variant",
    "intergenic_variant",
    "regulatory_region_variant",
    "regulatory_region_amplification",
    "regulatory_region_ablation",
    "TF_binding_site_variant",
    "TFBS_amplification",
    "TFBS_ablation",
    "downstream_gene_variant",
    "upstream_gene_variant",
    "coding_transcript_variant",
    "non_coding_transcript_variant",
    "NMD_transcript_variant",
    "intron_variant",
    "non_coding_transcript_exon_variant",
    "3_prime_UTR_variant",
    "5_prime_UTR_variant",
    "mature_miRNA_variant",
    "coding_sequence_variant",
    "synonymous_variant",
    "stop_retained_variant",
    "start_retained_variant",
    "incomplete_terminal_codon_variant",
    "splice_polypyrimidine_tract_variant",
    "splice_donor_region_variant",
    "splice_region_variant",
    "splice_donor_5th_base_variant",
    "protein_altering_variant",
    "missense_variant",
    "inframe_deletion",
    "inframe_insertion",
    "feature_truncation",
    "feature_elongation",
    "transcript_amplification",
    "start_lost",
    "stop_lost",
    "frameshift_variant",
    "stop_gained",
    "splice_donor_variant",
    "splice_acceptor_variant",
    "transcript_ablation",
])}

IMPACTS = {
    "HIGH": 3,
    "MODERATE": 2,
    "LOW": 1,
    "MODIFIER": 0,
}


class VEPAnnotatorBase(AnnotatorBase):
    """
    Base class for VEP annotators

    Provides utilities for preparing and parsing files for VEP
    """
    def __init__(
        self, pipeline: AnnotationPipeline | None,
        info: AnnotatorInfo,
        source_type_desc: dict[str, tuple[str, str]],
        extra_attributes: list[str] | None = None,
    ):
        if not info.attributes:
            attributes = [
                "Gene",
                "Feature",
                "Feature_type",
                "Consequence",
                "worst_consequence",
                "highest_impact",
                "gene_consequence",
            ]

            if extra_attributes is not None:
                attributes.extend(extra_attributes)

            info.attributes = AnnotationConfigParser.parse_raw_attributes(
                attributes)

        super().__init__(
            pipeline, info, source_type_desc=source_type_desc,
        )

    def _do_annotate(
        self, _annotatable: Annotatable | None,
        _context: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError(
            "External annotator supports only batch mode",
        )

    def annotate(
        self, _annotatable: Annotatable | None,
        _context: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError(
            "External annotator supports only batch mode",
        )

    def aggregate_attributes(
        self, contexts: list[dict[str, Any]],
        attr_name_list: list[str] | None = None,
    ) -> None:
        """Join list of attributes to display as one column in output."""
        if attr_name_list is None:
            attr_name_list = [attr.source for attr in self.attributes]

        for context in contexts:
            for attr in attr_name_list:
                context[attr] = ";".join(context[attr])

    def prepare_input(
        self, file: TextIO, annotatables: list[VCFAllele | None],
    ) -> None:
        """Prepare input files for VEP in standard VEP variant format."""
        writer = csv.writer(file, delimiter="\t")
        for idx, annotatable in enumerate(annotatables, 1):
            if annotatable is None:
                continue
            if annotatable.type in [
                Annotatable.Type.SMALL_DELETION,
                Annotatable.Type.SMALL_INSERTION,
            ]:
                if annotatable.type == Annotatable.Type.SMALL_DELETION:
                    ref_alt = f"{annotatable.ref[1:]}/-"
                else:
                    ref_alt = f"-/{annotatable.alt[1:]}"
                writer.writerow([
                    annotatable.chrom,
                    annotatable.pos + 1,
                    annotatable.end_position - 1,
                    ref_alt,
                    "+",
                    idx,
                ])
            else:
                writer.writerow([
                    annotatable.chrom,
                    annotatable.pos,
                    annotatable.end_position,
                    f"{annotatable.ref}/{annotatable.alt}",
                    "+",
                    idx,
                ])
        file.flush()

    def read_output(
        self, file: TextIO, contexts: list[dict[str, Any]],
        attributes: dict[str, Any],
    ) -> None:
        """Read and return subprocess output contents."""
        for context in contexts:
            for attr in attributes:
                context[attr] = []

        reader = csv.reader(
            filter(lambda row: not row.startswith("##"), file),
            delimiter="\t",
        )

        header = next(reader)[1:]
        columns_map = dict(enumerate(header))

        for row in reader:
            idx = int(row[0]) - 1
            context = contexts[idx]

            for idx, col in enumerate(row[1:]):
                col_name = columns_map[idx]
                context[col_name].append(col)

        for context in contexts:
            gene_consequences = []
            for gene, consequence in zip(
                context["SYMBOL"], context["Consequence"], strict=True,
            ):
                gene_consequences.append(f"{gene}:{consequence}")
            context["gene_consequence"] = gene_consequences

            consequences: list[str] = []
            for conseq in context["Consequence"]:
                consequences.extend(conseq.split(","))

            context["worst_consequence"] = [sorted(
                consequences, key=lambda x: CONSEQUENCES[x],
                reverse=True,
            )[0]]
            context["highest_impact"] = [sorted(
                context["IMPACT"], key=lambda x: IMPACTS[x],
                reverse=True,
            )[0]]

    def run_vep(self, args: list[str]) -> None:
        command = ["vep"]
        command.extend(args)
        subprocess.run(command, check=True)

    def open_files(self, work_dir: Path) -> tuple[TextIO, TextIO]:
        return (
            (work_dir / "input.tsv").open("w+t"),
            (work_dir / "output.tsv").open("w+t"),
        )


class VEPCacheAnnotator(VEPAnnotatorBase):
    """Annotation pipeline adapter for dummy_annotate using tempfiles."""

    def __init__(
        self, pipeline: AnnotationPipeline | None,
        info: AnnotatorInfo,
    ):
        self.vep_cache_dir: Path | None = cast(
            Path | None, info.parameters.get("cache_dir"),
        )

        assert self.vep_cache_dir is not None
        super().__init__(
            pipeline, info, full_attributes,
        )

    def _do_batch_annotate(
        self, annotatables: list[Annotatable | None],
        contexts: list[dict[str, Any]],
        batch_work_dir: str | None = None,
    ) -> list[dict[str, Any]]:
        if batch_work_dir is None:
            work_dir = self.work_dir
        else:
            work_dir = self.work_dir / batch_work_dir
        os.makedirs(work_dir, exist_ok=True)
        input_file, out_file = self.open_files(work_dir)
        with input_file, out_file:
            self.prepare_input(
                input_file, cast(list[VCFAllele | None], annotatables),
            )
            args = [
                "-i", cast(str, input_file.name),
                "-o", cast(str, out_file.name),
                "--tab", "--cache",
                "--offline",
                "--dir", str(self.vep_cache_dir),
                "--everything",
                "--symbol",
                "--no_stats",
                "--force_overwrite",
            ]
            self.run_vep(args)
            out_file.flush()
            self.read_output(out_file, contexts, full_attributes)

        self.aggregate_attributes(contexts)

        return contexts


class VEPEffectAnnotator(VEPAnnotatorBase):
    """Annotation pipeline adapter for dummy_annotate using tempfiles."""

    def __init__(
        self, pipeline: AnnotationPipeline | None,
        info: AnnotatorInfo,
    ):
        self.work_dir: Path = cast(Path, info.parameters.get("work_dir"))

        genome_id: str | None = info.parameters.get("genome")
        assert genome_id is not None
        gene_models_id: str | None = info.parameters.get("gene_models")
        assert gene_models_id is not None
        assert pipeline is not None
        self.cache_repo = GenomicResourceCachedRepo(
            pipeline.repository, str(self.work_dir / "grr_cache"),
        )

        self.genome_resource = self.cache_repo.get_resource(genome_id)
        self.genome_filename = \
            self.genome_resource.get_config()["filename"]

        self.gene_models_resource = self.cache_repo.get_resource(
            gene_models_id,
        )

        gtf_file_name = self.gene_models_resource.resource_id.replace("/", "_")

        self.gtf_path = self.work_dir / f"{gtf_file_name}.gtf"
        self.gtf_path_gz = self.gtf_path.with_suffix(
                f"{self.gtf_path.suffix}.gz",
            )

        self.annotator_attributes = copy.deepcopy(effect_attributes)
        self.annotator_attributes[self.gtf_path_gz.name] = (
            "object",
            f"Value from {self.gene_models_resource.resource_id}",
        )
        super().__init__(
            pipeline, info, self.annotator_attributes,
            [self.gtf_path_gz.name],
        )

        if not self.gtf_path_gz.exists():
            gene_models = build_gene_models_from_resource(
                self.gene_models_resource,
            )

            gene_models.load()
            gtf_content = gene_models_to_gtf(gene_models).getvalue()

            self.gtf_path.write_text(gtf_content)

            subprocess.run(["bgzip", str(self.gtf_path)], check=True)
            subprocess.run(
                ["tabix", "-p", "gff", str(self.gtf_path_gz)],
                check=True,
            )

    def _do_batch_annotate(
        self, annotatables: list[Annotatable | None],
        contexts: list[dict[str, Any]],
        batch_work_dir: str | None = None,
    ) -> list[dict[str, Any]]:
        genome_filepath = fsspec.url_to_fs(
            self.genome_resource.get_file_url(self.genome_filename),
        )[1]
        self.genome_resource.get_file_url(f"{self.genome_filename}.fai")

        if batch_work_dir is None:
            work_dir = self.work_dir
        else:
            work_dir = self.work_dir / batch_work_dir
        os.makedirs(work_dir, exist_ok=True)
        input_file, out_file = self.open_files(work_dir)
        with input_file, out_file:
            self.prepare_input(
                input_file, cast(list[VCFAllele | None], annotatables),
            )
            args = [
                "-i", input_file.name,
                "-o", out_file.name,
                "--tab",
                "--fasta", genome_filepath,
                "--gtf", self.gtf_path_gz,
                "--no_stats",
                "--symbol",
                "--force_overwrite",
            ]
            self.run_vep(args)
            out_file.flush()
            self.read_output(out_file, contexts, self.annotator_attributes)

        self.aggregate_attributes(contexts)

        return contexts


def build_vep_cache_annotator(
    pipeline: AnnotationPipeline,
    info: AnnotatorInfo,
) -> Annotator:
    return VEPCacheAnnotator(pipeline, info)


def build_vep_effect_annotator(
    pipeline: AnnotationPipeline,
    info: AnnotatorInfo,
) -> Annotator:
    return VEPEffectAnnotator(pipeline, info)
