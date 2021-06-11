from builtins import NotImplementedError
import sys
import traceback
import logging

import pandas as pd

from copy import deepcopy

from dae.configuration.gpf_config_parser import GPFConfigParser, FrozenBox
from dae.annotation.tools.utils import LineMapper

from dae.utils.dae_utils import dae2vcf_variant
from dae.variants.variant import SummaryAllele


logger = logging.getLogger(__name__)


class AnnotatorBase(object):

    """
    `AnnotatorBase` is base class of all `Annotators`.
    """

    def __init__(self, config, genomes_db, liftover=None):
        self.config = config
        self.genomes_db = genomes_db
        self.genomic_sequence = self.genomes_db.load_genomic_sequence(
            config.options.Graw
        )
        self.gene_models = self.genomes_db.load_gene_models(
            config.options.Traw, config.options.TrawFormat)

        assert self.genomes_db is not None
        assert self.genomic_sequence is not None
        assert self.gene_models is not None

        self.mode = "replace"
        if self.config.options.mode == "replace":
            self.mode = "replace"
        elif self.config.options.mode == "append":
            self.mode = "append"
        elif self.config.options.mode == "overwrite":
            self.mode = "overwrite"

        self.liftover = liftover

    def build_output_line(self, annotation_line):
        output_columns = self.config.output_columns
        return [annotation_line.get(key, "") for key in output_columns]

    def collect_annotator_schema(self, schema):
        # raise NotImplementedError()
        pass

    def annotate_file(self, file_io_manager):
        """
            Method for annotating file from `Annotator`.
        """
        self.schema = deepcopy(file_io_manager.reader.schema)
        self.collect_annotator_schema(self.schema)

        file_io_manager.writer.schema = self.schema

        line_mapper = LineMapper(file_io_manager.header)
        if self.mode == "replace":
            output_columns = [
                col
                for col in self.schema.columns
                if col not in self.config.virtual_columns
            ]

            # FIXME
            # Using this hack to change the output_columns
            # since the FrozenBox instances in "sections"
            # don't allow changing attributes via the standard
            # way with the usage of recusrive_dict_update
            self.config = self.config.to_dict()
            self.config["output_columns"] = output_columns
            self.config = FrozenBox(self.config)

        file_io_manager.header_write(self.config.output_columns)

        for line in file_io_manager.lines_read_iterator():
            # TODO How will additional headers behave
            # with column type support (and coercion)?
            if "#" in line[0]:
                file_io_manager.line_write(line)
                continue
            annotation_line = line_mapper.map(line)

            try:
                self.line_annotation(annotation_line)
            except Exception as ex:
                logger.error(f"problems annotating line: {line}")
                logger.error(f"{annotation_line}")
                logger.error(f"{ex}")
                traceback.print_exc(file=sys.stderr)

            file_io_manager.line_write(self.build_output_line(annotation_line))

    def annotate_df(self, df):
        result = []
        for line in df.to_dict(orient="records"):
            self.line_annotation(line)
            result.append(line)

        res_df = pd.DataFrame.from_records(result)
        return res_df

    def line_annotation(self, annotation_line):
        """
            Method returning annotations for the given line
            in the order from new_columns parameter.
        """
        raise NotImplementedError()


class CopyAnnotator(AnnotatorBase):
    def __init__(self, config, genomes_db):
        super(CopyAnnotator, self).__init__(config, genomes_db)

    def collect_annotator_schema(self, schema):
        for key, value in self.config.columns.items():
            assert key in schema.columns, [key, schema.columns]
            schema.columns[value] = schema.columns[key]

    def line_annotation(self, annotation_line, variant=None):
        data = {}
        for key, value in self.config.columns.items():
            data[value] = annotation_line[key]
        annotation_line.update(data)


class VariantAnnotatorBase(AnnotatorBase):
    def __init__(self, config, genomes_db):
        super(VariantAnnotatorBase, self).__init__(config, genomes_db)

        if not self.config.virtual_columns:
            self.config = GPFConfigParser.modify_tuple(
                self.config,
                {
                    "virtual_columns": [
                        "CSHL_location",
                        "CSHL_chr",
                        "CSHL_position",
                        "CSHL_variant",
                        "VCF_chr",
                        "VCF_position",
                        "VCF_ref",
                        "VCF_alt",
                    ]
                },
            )

    def collect_annotator_schema(self, schema):
        for vcol in self.config.virtual_columns:
            if "position" in vcol:
                schema.create_column(vcol, "int")
            else:
                schema.create_column(vcol, "str")

    def line_annotation(self, aline):
        variant = self.variant_builder.build(aline)
        logger.debug(f"line_annotation calls do_annotate({variant}")
        liftover_variants = {}
        self.do_annotate(aline, variant, liftover_variants)

    def do_annotate(self, aline, variant, liftover_variants):
        raise NotImplementedError()

    def annotate_summary_variant(self, summary_variant, liftover_variants):
        for alt_allele in summary_variant.alt_alleles:
            attributes = deepcopy(alt_allele.attributes)
            liftover_variants = {}
            self.do_annotate(attributes, alt_allele, liftover_variants)
            alt_allele.update_attributes(attributes)


class CompositeVariantAnnotator(VariantAnnotatorBase):
    def __init__(self, config, genomes_db):
        super(CompositeVariantAnnotator, self).__init__(config, genomes_db)
        self.annotators = []

    def add_annotator(self, annotator):
        assert isinstance(annotator, VariantAnnotatorBase)
        self.annotators.append(annotator)

    def do_annotate(self, aline, variant, liftover_variants):
        try:
            for annotator in self.annotators:
                annotator.do_annotate(aline, variant, liftover_variants)
        except Exception:
            logger.exception(
                f"cant annotate variant {variant}; source line {aline}")

    def collect_annotator_schema(self, schema):
        super(CompositeVariantAnnotator, self).collect_annotator_schema(schema)
        for annotator in self.annotators:
            annotator.collect_annotator_schema(schema)
