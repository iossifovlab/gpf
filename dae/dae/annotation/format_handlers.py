import gzip
import io
import logging
from abc import abstractmethod
from collections.abc import Generator, Iterable
from itertools import islice, starmap
from pathlib import Path
from typing import Any

from pysam import TabixFile, VariantFile, VariantRecord

from dae.annotation.annotatable import Annotatable, VCFAllele
from dae.annotation.annotation_config import (
    AttributeInfo,
    RawPipelineConfig,
)
from dae.annotation.annotation_factory import (
    build_annotation_pipeline,
)
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    ReannotationPipeline,
)
from dae.annotation.record_to_annotatable import (
    RecordToAnnotable,
    build_record_to_annotatable,
)
from dae.genomic_resources.reference_genome import (
    ReferenceGenome,
    build_reference_genome_from_resource,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.parquet.schema2.loader import ParquetLoader
from dae.parquet.schema2.parquet_io import VariantsParquetWriter
from dae.schema2_storage.schema2_layout import Schema2DatasetLayout
from dae.utils.regions import (
    Region,
)
from dae.variants.variant import SummaryVariant

logger = logging.getLogger("format_handlers")


def stringify(value: Any, *, vcf: bool = False) -> str:
    """Format the value to a string for human-readable output."""
    if value is None:
        return "." if vcf else ""
    if isinstance(value, float):
        return f"{value:.3g}"
    if isinstance(value, bool):
        return "yes" if value else ""
    return str(value)


class AbstractFormat:
    """
    Abstract class of input/output handlers for various formats.

    This class and its children are responsible for correctly reading from
    and writing to formats that can be annotated by our system.

    They convert the raw input data to types that can be passed to the
    annotation pipeline and then convert it back to its native format, as well
    as handling the reading, updating and writing of metadata the format may
    possess.

    Each child class handles the specific differences of a single format.
    """

    def __init__(
        self,
        pipeline_config: RawPipelineConfig,
        pipeline_config_old: str | None,
        cli_args: dict,
        grr_definition: dict | None,
        region: Region | None,
    ):
        self.pipeline: AnnotationPipeline | None = None
        self.grr: GenomicResourceRepo | None = None
        self.grr_definition = grr_definition
        self.pipeline_config = pipeline_config
        self.pipeline_config_old = pipeline_config_old
        self.cli_args = cli_args
        self.region = region
        if self.cli_args.get("reannotate"):
            pipeline_config_old = Path(self.cli_args["reannotate"]).read_text()

    def open(self) -> None:
        """
        Initialize all member variables and process relevant metadata.
        """
        self.grr = \
            build_genomic_resource_repository(definition=self.grr_definition)
        self.pipeline = build_annotation_pipeline(
            self.pipeline_config, self.grr,
            allow_repeated_attributes=self.cli_args[
                "allow_repeated_attributes"],
            work_dir=Path(self.cli_args["work_dir"]),
            config_old_raw=self.pipeline_config_old,
            full_reannotation=self.cli_args["full_reannotation"],
        )
        if self.pipeline is None:
            raise ValueError("No annotation pipeline was produced!")
        assert self.pipeline is not None
        self.pipeline.open()

    def close(self) -> None:
        """
        Close any open files, clean up anything unnecessary.
        """
        self.pipeline.close()  # type: ignore

    @abstractmethod
    def _read(self) -> Generator[Any, None, None]:
        """
        Read raw data from the input.
        """

    @abstractmethod
    def _convert(self, variant: Any) -> list[tuple[Annotatable, dict]]:
        """
        Convert a single piece of raw data from the input into a usable format.

        This method returns a list of tuples - one tuple per allele for the raw
        variant data that has been read.

        Each tuple contains an Annotatable instance, which will be
        annotated by the relevant annotation pipeline, and a dictionary
        containing any attributes already present in the raw data, such as a
        previous annotation - this is called a "context". This "context" is
        primarily used when reannotating data.
        """

    @abstractmethod
    def _apply(self, variant: Any, annotations: list[dict]) -> None:
        """
        Apply produced annotations to the raw variant data.

        This method updates the native variant data in-place with a list of
        annotations - this list should contain a dictionary of annotation
        results for each allele in the variant.
        """

    @abstractmethod
    def _write(self, variant: Any) -> None:
        """
        Write a single piece of raw data to the output.
        """

    @staticmethod
    def get_task_dir(region: Region | None) -> str:
        """Get dir for batch annotation."""
        if region is None:
            return "batch_work_dir"
        chrom = region.chrom
        pos_beg = region.start if region.start is not None else "_"
        pos_end = region.stop if region.stop is not None else "_"
        return f"{chrom}_{pos_beg}_{pos_end}"

    def process(self) -> None:
        """
        Iteratively carry out the annotation of the input.

        This method will read, annotate, apply and then write each variant
        from the input data in an iterative fashion - one by one.
        """
        assert self.pipeline is not None
        annotations = []
        for variant in self._read():
            try:
                annotations = list(starmap(self.pipeline.annotate,
                                           self._convert(variant)))
                self._apply(variant, annotations)
                self._write(variant)
            except Exception:  # pylint: disable=broad-except
                logger.exception("Error during iterative annotation")

    def process_batched(self) -> None:
        """
        Carry out the annotation of the input in batches.

        This method performs each step of the read-annotate-apply-write
        loop in batches.
        """
        assert self.pipeline is not None

        batch_size = self.cli_args["batch_size"]
        work_dir = AbstractFormat.get_task_dir(self.region)
        errors = []
        try:
            while batch := tuple(islice(self._read(), batch_size)):
                all_contexts = []
                all_annotatables = []
                allele_counts = []  # per variant

                for variant in batch:
                    annotatables, contexts = zip(*self._convert(variant),
                                                 strict=True)
                    all_contexts.extend(contexts)
                    all_annotatables.extend(annotatables)
                    allele_counts.append(len(annotatables))

                all_annotations = iter(self.pipeline.batch_annotate(
                    all_annotatables,
                    all_contexts,
                    batch_work_dir=work_dir,
                ))

                for variant, allele_count in zip(batch, allele_counts,
                                                 strict=True):
                    annotations = [next(all_annotations)
                                   for _ in range(allele_count)]
                    self._apply(variant, annotations)
                    self._write(variant)

        except Exception as ex:  # pylint: disable=broad-except
            logger.exception("Error during batch annotation")
            errors.append(str(ex))
        if len(errors) > 0:
            logger.error("there were errors during annotation")
            for error in errors:
                logger.error("\t%s", error)


class ColumnsFormat(AbstractFormat):
    """
    Handler for delimiter-separated values text files.
    """

    def __init__(
        self,
        pipeline_config: RawPipelineConfig,
        pipeline_config_old: str | None,
        cli_args: dict,
        grr_definition: dict | None,
        region: Region | None,
        input_path: str,
        output_path: str,
        ref_genome_id: str | None,
    ):
        super().__init__(pipeline_config, pipeline_config_old,
                         cli_args, grr_definition, region)
        self.input_path = input_path
        self.output_path = output_path
        self.ref_genome_id = ref_genome_id
        self.input_separator = cli_args["input_separator"]
        self.separator = cli_args["output_separator"]

        self.ref_genome: ReferenceGenome | None = None
        self.line_iterator: Iterable[str] | None = None
        self.header_columns: list[str] | None = None
        self.record_to_annotatable: RecordToAnnotable | None = None
        self.annotation_columns: list[str] | None = None
        self.input_file: TabixFile | io.TextIOBase | None = None
        self.output_file: io.TextIOBase | None = None

    def open(self) -> None:
        # pylint: disable=consider-using-with
        super().open()
        assert self.grr is not None
        if self.ref_genome_id:
            res = self.grr.find_resource(self.ref_genome_id)
            if res is not None:
                self.ref_genome = \
                    build_reference_genome_from_resource(res).open()

        # Open input file
        if self.input_path.endswith(".gz"):
            self.input_file = TabixFile(self.input_path)
            with gzip.open(self.input_path, "rt") as in_file_raw:
                raw_header = in_file_raw.readline()

            if self.region is not None:
                self.line_iterator = self.input_file.fetch(
                    self.region.chrom, self.region.start, self.region.stop)
            else:
                self.line_iterator = self.input_file.fetch()
        else:
            self.input_file = open(self.input_path, "rt")  # noqa: SIM115
            self.line_iterator = self.input_file
            raw_header = self.input_file.readline()

        # Set header columns
        self.header_columns = [
            c.strip("#")
            for c in raw_header.strip("\r\n").split(self.input_separator)
        ]

        self.record_to_annotatable = build_record_to_annotatable(
            self.cli_args, set(self.header_columns),
            ref_genome=self.ref_genome)

        assert self.pipeline is not None
        self.annotation_columns = [
            attr.name
            for attr in self.pipeline.get_attributes()
            if not attr.internal
        ]
        self.output_file = open(self.output_path, "w")  # noqa: SIM115

        # Write header to output file
        if isinstance(self.pipeline, ReannotationPipeline):
            old_annotation_columns = {
                attr.name
                for attr in self.pipeline.pipeline_old.get_attributes()
                if not attr.internal
            }
            new_header = [
                col for col in self.header_columns
                if col not in old_annotation_columns
            ]
        else:
            new_header = list(self.header_columns)
        new_header = new_header + self.annotation_columns
        self.output_file.write(self.separator.join(new_header) + "\n")

    def close(self) -> None:
        super().close()
        if self.input_file is not None:
            self.input_file.close()
        if self.output_file is not None:
            self.output_file.close()

    def _read(self) -> Generator[dict, None, None]:
        assert self.cli_args is not None
        assert self.header_columns is not None
        assert self.line_iterator is not None

        errors = []
        for lnum, line in enumerate(self.line_iterator):
            try:
                columns = line.strip("\n\r").split(self.input_separator)
                record = dict(zip(self.header_columns, columns, strict=True))
                yield record
            except Exception as ex:  # pylint: disable=broad-except
                logger.exception(
                    "unexpected input data format at line %s: %s",
                    lnum, line)
                errors.append((lnum, line, str(ex)))

        if len(errors) > 0:
            logger.error("there were errors during the import")
            for lnum, line, error in errors:
                logger.error("line %s: %s", lnum, line)
                logger.error("\t%s", error)

    def _apply(self, variant: dict, annotations: list[dict]) -> None:
        if isinstance(self.pipeline, ReannotationPipeline):
            for col in self.pipeline.attributes_deleted:
                del variant[col]

        # No support for multi-allelic variants in columns format
        annotation = annotations[0]

        for col in self.annotation_columns:  # type: ignore
            variant[col] = annotation[col]

    def _convert(self, variant: dict) -> list[tuple[Annotatable, dict]]:
        return [(
            self.record_to_annotatable.build(variant),  # type: ignore
            dict(variant))]

    def _write(self, variant: dict) -> None:
        result = self.separator.join(
            stringify(val) for val in variant.values()
        ) + "\n"
        self.output_file.write(result)  # type: ignore


class VCFFormat(AbstractFormat):
    """
    Handler for VCF format files.
    """

    def __init__(
        self,
        pipeline_config: RawPipelineConfig,
        pipeline_config_old: str | None,
        cli_args: dict,
        grr_definition: dict | None,
        region: Region | None,
        input_path: str,
        output_path: str,
    ):
        super().__init__(pipeline_config, pipeline_config_old,
                         cli_args, grr_definition, region)
        self.input_path = input_path
        self.output_path = output_path

        self.input_file: VariantFile | None = None
        self.output_file: VariantFile | None = None
        self.annotation_attributes: list[AttributeInfo] | None = None

    @staticmethod
    def _update_header(
        variant_file: VariantFile,
        pipeline: AnnotationPipeline | ReannotationPipeline,
        args: dict,
    ) -> None:
        """Update a variant file's header with annotation pipeline scores."""
        header = variant_file.header
        header.add_meta("pipeline_annotation_tool", "GPF variant annotation.")
        header.add_meta("pipeline_annotation_tool", f"{args}")
        if isinstance(pipeline, ReannotationPipeline):
            header_info_keys = variant_file.header.info.keys()
            old_annotation_columns = {
                attr.name for attr in pipeline.pipeline_old.get_attributes()
                if not attr.internal
            }
            new_annotation_columns = {
                attr.name for attr in pipeline.get_attributes()
                if not attr.internal
            }

            for info_key in header_info_keys:
                if info_key in old_annotation_columns \
                        and info_key not in new_annotation_columns:
                    variant_file.header.info.remove_header(info_key)

            attributes = []
            for attr in pipeline.get_attributes():
                if attr.internal:
                    continue

                if attr.name not in variant_file.header.info:
                    attributes.append(attr)
        else:
            attributes = pipeline.get_attributes()

        for attribute in attributes:
            description = attribute.description
            description = description.replace("\n", " ")
            description = description.replace('"', '\\"')
            header.info.add(attribute.name, "A", "String", description)

    def open(self) -> None:
        super().open()
        assert self.pipeline is not None
        self.annotation_attributes = self.pipeline.get_attributes()

        self.input_file = VariantFile(self.input_path, "r")
        assert self.input_file is not None
        VCFFormat._update_header(self.input_file, self.pipeline, self.cli_args)
        self.output_file = VariantFile(self.output_path, "w",
                                       header=self.input_file.header)

    def close(self) -> None:
        super().close()
        self.input_file.close()  # type: ignore
        self.output_file.close()  # type: ignore

    def _read(self) -> Generator[Any, None, None]:
        assert self.input_file is not None

        if self.region is None:
            in_file_iter = self.input_file.fetch()
        else:
            in_file_iter = self.input_file.fetch(
                self.region.chrom, self.region.start, self.region.stop)

        for vcf_var in in_file_iter:
            if vcf_var.ref is None:
                logger.warning(
                    "vcf variant without reference: %s %s",
                    vcf_var.chrom, vcf_var.pos,
                )
                continue

            if vcf_var.alts is None:
                logger.info(
                    "vcf variant without alternatives: %s %s",
                    vcf_var.chrom, vcf_var.pos,
                )
                continue

            yield vcf_var

    def _convert(
        self, variant: VariantRecord,
    ) -> list[tuple[Annotatable, dict]]:
        return [
            (VCFAllele(
                variant.chrom, variant.pos,
                variant.ref, alt),  # type: ignore
             dict(variant.info))
            for alt in variant.alts  # type: ignore
        ]

    def _apply(self, variant: VariantRecord, annotations: list[dict]) -> None:
        VCFFormat._update_vcf_variant(
            variant, annotations,
            self.annotation_attributes,  # type: ignore
            self.pipeline,  # type: ignore
        )

    def _write(self, variant: VariantRecord) -> None:
        self.output_file.write(variant)  # type: ignore

    @staticmethod
    def _update_vcf_variant(
        vcf_var: VariantRecord,
        allele_annotations: list,
        attributes: list[AttributeInfo],
        pipeline: AnnotationPipeline,
    ) -> None:
        buffers: list[list] = [[] for _ in attributes]
        for annotation in allele_annotations:
            if isinstance(pipeline, ReannotationPipeline):
                for col in pipeline.attributes_deleted:
                    del vcf_var.info[col]

            for buff, attribute in zip(buffers, attributes, strict=True):
                attr = annotation.get(attribute.name)
                if isinstance(attr, list):
                    attr = ";".join(stringify(a, vcf=True) for a in attr)
                elif isinstance(attr, dict):
                    attr = ";".join(
                        f"{k}:{v}"
                        for k, v in attr.items()
                    )
                else:
                    attr = stringify(attr, vcf=True)
                attr = stringify(attr, vcf=True) \
                    .replace(";", "|")\
                    .replace(",", "|")\
                    .replace(" ", "_")
                buff.append(attr)
        # If the all values for a given attribute are
        # empty (i.e. - "."), then that attribute has no
        # values to be written and will be skipped in the output
        has_value = {
            attr.name: any(filter(lambda x: x != ".", buffers[idx]))
            for idx, attr in enumerate(attributes)
        }
        for buff, attribute in zip(buffers, attributes, strict=True):
            if attribute.internal or not has_value[attribute.name]:

                continue
            vcf_var.info[attribute.name] = buff


class ParquetFormat(AbstractFormat):
    """
    Handler for Schema2 Parquet datasets.
    """

    def __init__(
        self,
        pipeline_config: RawPipelineConfig,
        pipeline_config_old: str | None,
        cli_args: dict,
        grr_definition: dict | None,
        region: Region | None,
        input_layout: Schema2DatasetLayout,
        output_dir: str,
        bucket_idx: int,
        variants_blob_serializer: str = "json",
    ):
        super().__init__(pipeline_config, pipeline_config_old,
                         cli_args, grr_definition, region)
        self.input_layout = input_layout
        self.output_dir = output_dir
        self.bucket_idx = bucket_idx

        self.input_loader: ParquetLoader | None = None
        self.writer: VariantsParquetWriter | None = None
        self.internal_attributes: list[str] | None = None
        self.variants_blob_serializer = variants_blob_serializer

    def open(self) -> None:
        super().open()
        assert self.pipeline is not None
        self.input_loader = ParquetLoader(self.input_layout)
        self.writer = VariantsParquetWriter(
            self.output_dir, self.pipeline,
            self.input_loader.partition_descriptor,
            bucket_index=self.bucket_idx,
            variants_blob_serializer=self.variants_blob_serializer,
        )
        if isinstance(self.pipeline, ReannotationPipeline):
            self.internal_attributes = [
                attribute.name
                for annotator in (self.pipeline.annotators_new
                                  | self.pipeline.annotators_rerun)
                for attribute in annotator.attributes
                if attribute.internal
            ]
        else:
            self.internal_attributes = [
                attribute.name
                for attribute in self.pipeline.get_attributes()
                if attribute.internal
            ]

    def close(self) -> None:
        super().close()
        assert self.writer is not None
        self.writer.close()

    def _read(self) -> Generator[SummaryVariant, None, None]:
        assert self.input_loader is not None
        yield from self.input_loader.fetch_summary_variants(region=self.region)

    def _convert(
        self, variant: SummaryVariant,
    ) -> list[tuple[Annotatable, dict]]:
        return [(allele.get_annotatable(), allele.attributes)
                for allele in variant.alt_alleles]

    def _apply(self, variant: SummaryVariant, annotations: list[dict]) -> None:
        for allele, annotation in zip(variant.alt_alleles, annotations,
                                      strict=True):
            if isinstance(self.pipeline, ReannotationPipeline):
                for attr in self.pipeline.attributes_deleted:
                    del allele.attributes[attr]
            for attr in self.internal_attributes:  # type: ignore
                del annotation[attr]
            allele.update_attributes(annotation)

    def _write(self, variant: SummaryVariant) -> None:
        assert self.internal_attributes is not None
        assert self.writer is not None
        self.writer.write_summary_variant(variant)
