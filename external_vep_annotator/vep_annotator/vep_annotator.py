from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path
from typing import Any, TextIO

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
    ):
        if not info.attributes:
            info.attributes = AnnotationConfigParser.parse_raw_attributes([
                "gene",
                "feature",
                "feature_type",
                "consequence",
                "worst_consequence",
                "highest_impact",
                "gene_consequence",
            ])

        super().__init__(
            pipeline, info, {
                "gene": ("object", "Gene symbol reported by VEP"),
                "gene_id": ("object", "Gene ID reported by VEP"),
                "feature": ("object", ""),
                "feature_type": ("object", ""),
                "consequence": ("object", "VEP effect type"),
                "location": ("object", "VEP location"),
                "allele": ("object", "VEP allele"),
                "cdna_position": ("object", "VEP cDNA position"),
                "cds_position": ("object", "VEP cds position"),
                "protein_position": ("object", "VEP protein position"),
                "amino_acids": ("object", "Amino acids reported by VEP"),
                "codons": ("object", "Codons reported by VEP"),
                "existing_variation": (
                    "object", "Existing variation reported by VEP",
                ),
                "impact": ("object", "Variant impact reported by VEP"),
                "distance": ("object", "Distance reported by VEP"),
                "strand": ("int", "Variant impact reported by VEP"),
                "symbol_source": ("object", "VEP gene symbol source"),
                "worst_consequence": (
                    "object", "Worst consequence reported by VEP",
                ),
                "highest_impact": ("object", "Highest impact reported by VEP"),
                "gene_consequence": (
                    "object", "List of gene consequence pairs reported by VEP",
                ),
            },
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
    ) -> None:
        """Read and return subprocess output contents."""
        for context in contexts:
            context["gene"] = []
            context["gene_id"] = []
            context["feature"] = []
            context["feature_type"] = []
            context["consequence"] = []
            context["location"] = []
            context["allele"] = []
            context["cdna_position"] = []
            context["cds_position"] = []
            context["protein_position"] = []
            context["amino_acids"] = []
            context["codons"] = []
            context["existing_variation"] = []
            context["impact"] = []
            context["distance"] = []
            context["strand"] = []
            context["symbol_source"] = []

        reader = csv.reader(
            filter(lambda row: row[0] != "#", file),
            delimiter="\t",
        )

        for row in reader:
            idx = int(row[0]) - 1
            context = contexts[idx]
            context["allele"].append(row[1])
            context["location"].append(row[2])
            context["gene_id"].append(row[3])
            context["feature"].append(row[4])
            context["feature_type"].append(row[5])
            context["consequence"].append(row[6])
            context["cdna_position"].append(row[7])
            context["cds_position"].append(row[8])
            context["protein_position"].append(row[9])
            context["amino_acids"].append(row[10])
            context["codons"].append(row[11])
            context["existing_variation"].append(row[12])
            context["impact"].append(row[13])
            context["distance"].append(row[14])
            context["strand"].append(row[15])
            context["gene"].append(row[17])
            context["symbol_source"].append(row[18])

        for context in contexts:
            gene_consequences = []
            for gene, consequence in zip(
                context["gene"], context["consequence"], strict=True,
            ):
                gene_consequences.append(f"{gene}:{consequence}")
            context["gene_consequence"] = gene_consequences

            the_consequences: list[str] = []
            for conseq in context["consequence"]:
                the_consequences.extend(conseq.split(","))

            context["worst_consequence"] = [sorted(
                the_consequences, key=lambda x: CONSEQUENCES[x],
            )[0]]
            context["highest_impact"] = [sorted(
                context["impact"], key=lambda x: IMPACTS[x],
            )[0]]


class VEPCacheAnnotator(VEPAnnotatorBase):
    """Annotation pipeline adapter for dummy_annotate using tempfiles."""

    def __init__(
        self, pipeline: AnnotationPipeline | None,
        info: AnnotatorInfo,
    ):
        self.vep_cache_dir: Path = info.parameters.get("cache_dir")

        super().__init__(
            pipeline, info,
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
        with (work_dir / "input.tsv").open("w+t") as input_file, \
                (work_dir / "output.tsv").open("w+t") as out_file:
            self.prepare_input(input_file, annotatables)
            args = [
                "vep", "-i", input_file.name,
                "-o", out_file.name,
                "--tab", "--cache",
                "--dir", self.vep_cache_dir,
                "--symbol",
                "--no_stats",
                "--force_overwrite",
            ]
            subprocess.run(args, check=True)
            out_file.flush()
            self.read_output(out_file, contexts)

        self.aggregate_attributes(contexts)

        return contexts


class VEPEffectAnnotator(VEPAnnotatorBase):
    """Annotation pipeline adapter for dummy_annotate using tempfiles."""

    def __init__(
        self, pipeline: AnnotationPipeline | None,
        info: AnnotatorInfo,
    ):
        super().__init__(
            pipeline, info,
        )

        genome_id = info.parameters.get("genome")
        gene_models_id = info.parameters.get("gene_models")
        self.cache_repo = GenomicResourceCachedRepo(
            pipeline.repository, self.work_dir / "grr_cache",
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

        if not self.gtf_path_gz.exists():
            gene_models = build_gene_models_from_resource(
                self.gene_models_resource,
            )

            gene_models.load()
            gtf_content = gene_models_to_gtf(gene_models)

            self.gtf_path.write_text(gtf_content)

            subprocess.run(["bgzip", str(self.gtf_path)], check=True)
            subprocess.run(
                ["tabix", "-p", "gff", str(self.gtf_path_gz)],
                check=True,
            )

    def _do_batch_annotate(
        self, annotatables: list[Annotatable] | None,
        contexts: list[dict[str, Any]],
        batch_work_dir: [Path] = None,
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
        with (work_dir / "input.tsv").open("w+t") as input_file, \
                (work_dir / "output.tsv").open("w+t") as out_file:
            self.prepare_input(input_file, annotatables)
            args = [
                "vep", "-i", input_file.name,
                "-o", out_file.name,
                "--tab",
                "--fasta", genome_filepath,
                "--gtf", self.gtf_path_gz,
                "--no_stats",
                "--symbol",
                "--force_overwrite",
            ]
            subprocess.run(args, check=True)
            out_file.flush()
            self.read_output(out_file, contexts)

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
