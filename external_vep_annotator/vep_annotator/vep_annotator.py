from __future__ import annotations

import csv
import logging
import os
import subprocess
import textwrap
from collections.abc import Sequence
from pathlib import Path
from typing import Any, TextIO, cast

from dae.annotation.annotatable import Annotatable, VCFAllele
from dae.annotation.annotation_factory import AnnotationConfigParser
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    Annotator,
    AnnotatorInfo,
)
from dae.annotation.docker_annotator import DockerAnnotator
from dae.genomic_resources.cached_repository import GenomicResourceCachedRepo
from dae.genomic_resources.gene_models import (
    build_gene_models_from_resource,
    gene_models_to_gtf,
)
from dae.genomic_resources.repository import GenomicResource

from vep_annotator.vep_attributes import effect_attributes, full_attributes

logger = logging.getLogger(__name__)

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


class VEPAnnotatorBase(DockerAnnotator):
    """
    Base class for VEP annotators

    Provides utilities for preparing and parsing files for VEP
    """
    def __init__(
        self, pipeline: AnnotationPipeline | None,
        info: AnnotatorInfo,
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

        vep_version: str | None = info.parameters.get("vep_version", None)
        if vep_version is not None and not vep_version.find("."):
            vep_version = f"{vep_version}.0"
        if vep_version is None:
            vep_version = "release_latest"
        else:
            vep_version = f"release_{vep_version}"

        self._vep_version = vep_version

        super().__init__(
            pipeline, info,
        )

    def _init_images(self) -> None:
        if self._vep_version is not None:
            self.client.images.pull(
                f"ensemblorg/ensembl-vep:{self._vep_version}",
            )
        else:
            self.client.images.pull(
                "ensemblorg/ensembl-vep:release_latest",
            )

    def _do_annotate(
        self, annotatable: Annotatable | None,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError(
            "External annotator supports only batch mode",
        )

    def annotate(
        self, annotatable: Annotatable | None,
        context: dict[str, Any],
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
        writer = csv.writer(file, delimiter="\t", lineterminator="\n")
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
        unsupported_cols = {col for col in header if col not in contexts[0]}
        if len(unsupported_cols) > 0:
            logger.warning(
                "VEP annotator detected new unsupported columns: %s",
                unsupported_cols,
            )
        columns_map = dict(enumerate(header))

        for row in reader:
            idx = int(row[0]) - 1
            context = contexts[idx]

            for idx, col in enumerate(row[1:]):
                col_name = columns_map[idx]
                if col_name not in context:
                    continue
                context[col_name].append(col)

        for context in contexts:
            gene_consequences = set()
            gene_consequences.update([
                f"{gene}:{consequence}"
                for gene, consequence in
                zip(context["SYMBOL"], context["Consequence"], strict=True)
            ])
            context["gene_consequence"] = list(gene_consequences)
            context["gene_consequence"].sort()

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

    def open_files(self, work_dir: Path) -> tuple[TextIO, Path]:
        return (
            (work_dir / "input.tsv").open("w+t"),
            (work_dir / "output.tsv"),
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
            pipeline, info,
        )

        info.documentation += textwrap.dedent(f"""

            Ensembl VEP plugin annotator that annotates using VEP through
            a docker container with a prepared VEP cache.

            This annotator is configured to run with VEP version {self._vep_version}

        <a href="https://iossifovlab.com/gpfuserdocs/administration/annotation.html#vep-annotators" target="_blank">More info</a>

        """)  # noqa

    def _attribute_type_descs(self) -> dict[str, tuple[str, str]]:
        return full_attributes

    def _do_batch_annotate(
        self,
        annotatables: Sequence[Annotatable | None],
        contexts: list[dict[str, Any]],
        batch_work_dir: str | None = None,
    ) -> list[dict[str, Any]]:
        if batch_work_dir is None:
            work_dir = self.work_dir
        else:
            work_dir = self.work_dir / batch_work_dir
        os.makedirs(work_dir, exist_ok=True)
        work_dir.chmod(0o0777)
        input_file, out_path = self.open_files(work_dir)
        with input_file:
            self.prepare_input(
                input_file, cast(list[VCFAllele | None], annotatables),
            )

            self.run(
                input_file_name=Path(input_file.name).name,
                output_file_name=out_path.name,
                work_dir=str(work_dir.absolute()),
            )

        with out_path.open("r") as out_file:
            self.read_output(
                out_file, contexts, self._attribute_type_descs(),
            )

        self.aggregate_attributes(contexts)

        return contexts

    def run(self, **kwargs):
        args = [
            "vep",
            "-i", str(Path("/work", kwargs["input_file_name"])),
            "-o", str(Path("/work", kwargs["output_file_name"])),
            "--tab", "--cache",
            "--offline",
            "--dir", "/vep_cache",
            "--everything",
            "--symbol",
            "--no_stats",
            "--force_overwrite",
        ]
        self.client.containers.run(
            f"ensemblorg/ensembl-vep:{self._vep_version}",
            args,
            volumes={
                kwargs["work_dir"]: {"bind": "/work", "mode": "rw"},
                str(self.vep_cache_dir): {"bind": "/vep_cache", "mode": "ro"},
            },
        )


class VEPEffectAnnotator(VEPAnnotatorBase):
    """Annotation pipeline adapter for dummy_annotate using tempfiles."""

    def __init__(
        self, pipeline: AnnotationPipeline | None,
        info: AnnotatorInfo,
    ):
        self.work_dir: Path = cast(Path, info.parameters.get("work_dir"))

        assert pipeline is not None

        self.cache_repo = GenomicResourceCachedRepo(
            pipeline.repository, str(self.work_dir / "grr_cache"),
        )
        self.genome_filename = None
        self.gtf_path = None
        self.gtf_path_gz = None
        self.gene_models_resource = None
        self.genome_resource = None

        self.annotator_attributes = effect_attributes

        pipeline_context = pipeline.build_pipeline_genomic_context()

        gene_models_id: str | None = info.parameters.get("gene_models")
        if gene_models_id is not None:
            self.gene_models_resource = self.cache_repo.get_resource(
                gene_models_id,
            )
        else:
            gene_models = pipeline_context.get_gene_models()
            if gene_models is None:
                raise ValueError(
                    f"No gene models found for {info.annotator_id}",
                )
            self.gene_models_resource = gene_models.resource
        genome_id: str | None = info.parameters.get("genome")

        gene_model_genome_id = self.gene_models_resource.get_labels().get(
            "reference_genome",
        )
        if genome_id is not None:
            self.genome_resource = self.cache_repo.get_resource(genome_id)
        elif gene_model_genome_id is not None:
            self.genome_resource = self.cache_repo.get_resource(
                gene_model_genome_id)
        else:
            genome = pipeline_context.get_reference_genome()
            if genome is None:
                raise ValueError(
                    f"No reference genome found for {info.annotator_id}",
                )
            self.genome_resource = genome.resource

        info.resources.append(self.gene_models_resource)
        info.resources.append(self.genome_resource)

        super().__init__(pipeline, info)

        info.documentation += textwrap.dedent(f"""

            Ensembl VEP plugin annotator that annotates using VEP through
            a docker container with GTF and FASTA files.

            This annotator is configured to run with VEP version {self._vep_version}

        <a href="https://iossifovlab.com/gpfuserdocs/administration/annotation.html#vep-annotators" target="_blank">More info</a>

        """)  # noqa

        self.resources_dir = (self.work_dir / "annotator_resources").absolute()
        self.resources_dir.mkdir(exist_ok=True)

    def find_gene_models(self) -> GenomicResource:
        """Find gene models from info or genomic context."""
        return cast(GenomicResource, self.gene_models_resource)

    def find_genome(self) -> GenomicResource:
        """Find genome from info, resource label or genomic context."""
        return cast(GenomicResource, self.genome_resource)

    def _attribute_type_descs(self) -> dict[str, tuple[str, str]]:
        return effect_attributes

    def _do_batch_annotate(
        self,
        annotatables: Sequence[Annotatable | None],
        contexts: list[dict[str, Any]],
        batch_work_dir: str | None = None,
    ) -> list[dict[str, Any]]:

        assert self.genome_resource is not None
        assert self.genome_filename is not None
        assert self.gtf_path_gz is not None

        self.genome_resource.get_file_url(self.genome_filename)
        self.genome_resource.get_file_url(f"{self.genome_filename}.fai")

        genome_filepath = Path(
            "/grr",
            self.genome_resource.get_genomic_resource_id_version(),
            self.genome_filename,
        )

        if batch_work_dir is None:
            work_dir = self.work_dir
        else:
            work_dir = self.work_dir / batch_work_dir
        os.makedirs(work_dir, exist_ok=True)
        work_dir.chmod(0o0777)
        input_file, out_path = self.open_files(work_dir)
        with input_file:
            self.prepare_input(
                input_file, cast(list[VCFAllele | None], annotatables),
            )
            self.run(
                input_file_name=Path(input_file.name).name,
                output_file_name=out_path.name,
                work_dir=str(work_dir.absolute()),
                genome_filepath=str(genome_filepath),
                gtf_filename=self.gtf_path_gz.name,
            )

        with out_path.open("r") as out_file:
            self.read_output(
                out_file, contexts, self._attribute_type_descs(),
            )

        self.aggregate_attributes(contexts)

        return contexts

    def run(self, **kwargs):
        assert self.genome_resource is not None
        args = [
            "vep",
            "-i", str(Path("/work", kwargs["input_file_name"])),
            "-o", str(Path("/work", kwargs["output_file_name"])),
            "--tab",
            "--fasta", str(Path("/grr", kwargs["genome_filepath"])),
            "--gtf", str(Path("/resources", kwargs["gtf_filename"])),
            "--symbol",
            "--no_stats",
            "--force_overwrite",
        ]
        cache_path = Path(self.genome_resource.proto.url[7:]).absolute()
        self.client.containers.run(
            f"ensemblorg/ensembl-vep:{self._vep_version}",
            args,
            volumes={
                kwargs["work_dir"]: {"bind": "/work", "mode": "rw"},
                str(cache_path): {"bind": "/grr", "mode": "ro"},
                str(self.resources_dir): {"bind": "/resources", "mode": "ro"},
            },
        )

    def open(self) -> Annotator:
        assert self.genome_resource is not None
        assert self.gene_models_resource is not None

        self.genome_filename = \
            self.genome_resource.get_config()["filename"]

        gtf_file_name = self.gene_models_resource.resource_id.replace("/", "_")

        self.gtf_path = self.resources_dir / f"{gtf_file_name}.gtf"
        self.gtf_path_gz = self.gtf_path.with_suffix(
                f"{self.gtf_path.suffix}.gz",
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

        return super().open()


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
