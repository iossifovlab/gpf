import gzip
import io
import logging
from abc import abstractmethod
from collections.abc import Generator, Iterable
from itertools import islice, starmap
from pathlib import Path
from typing import Any

from pysam import TabixFile

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotation_config import (
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
from dae.utils.regions import Region

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
