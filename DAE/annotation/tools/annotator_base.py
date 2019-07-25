import sys
import traceback

import pandas as pd

from copy import deepcopy

from annotation.tools.annotator_config import LineConfig, \
    AnnotatorConfig, \
    VariantAnnotatorConfig
from utils.dae_utils import dae2vcf_variant
from variants.variant import SummaryAllele
import GenomeAccess


class AnnotatorBase(object):

    """
    `AnnotatorBase` is base class of all `Annotators`.
    """

    def __init__(self, config):
        assert isinstance(config, AnnotatorConfig)

        self.config = config

        self.mode = "replace"
        if self.config.options.mode == "replace":
            self.mode = "replace"
        elif self.config.options.mode == "append":
            self.mode = "append"
        elif self.config.options.mode == "overwrite":
            self.mode = "overwrite"

    def build_output_line(self, annotation_line):
        output_columns = self.config.output_columns
        return [
            annotation_line.get(key, '') for key in output_columns
        ]

    def collect_annotator_schema(self, schema):
        raise NotImplementedError()

    def annotate_file(self, file_io_manager):
        """
            Method for annotating file from `Annotator`.
        """
        self.schema = deepcopy(file_io_manager.reader.schema)
        self.collect_annotator_schema(self.schema)
        file_io_manager.writer.schema = self.schema

        line_config = LineConfig(file_io_manager.header)
        if self.mode == 'replace':
            self.config.output_columns = \
                [col for col in self.schema.columns
                 if col not in self.config.virtual_columns]

        file_io_manager.header_write(self.config.output_columns)

        for line in file_io_manager.lines_read_iterator():
            # TODO How will additional headers behave
            # with column type support (and coercion)?
            if '#' in line[0]:
                file_io_manager.line_write(line)
                continue
            annotation_line = line_config.build(line)
            # print(annotation_line)

            try:
                self.line_annotation(annotation_line)
            except Exception:
                print("Problems annotating line:", line, file=sys.stderr)
                print(annotation_line, file=sys.stderr)
                traceback.print_exc(file=sys.stderr)

            file_io_manager.line_write(
                self.build_output_line(annotation_line))

    def annotate_df(self, df):
        result = []
        for line in df.to_dict(orient='records'):
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

    def __init__(self, config):
        super(CopyAnnotator, self).__init__(config)

    def collect_annotator_schema(self, schema):
        for key, value in self.config.columns_config.items():
            assert key in schema.columns, [key, schema.columns]
            schema.columns[value] = schema.columns[key]

    def line_annotation(self, annotation_line, variant=None):
        data = {}
        for key, value in self.config.columns_config.items():
            data[value] = annotation_line[key]
        annotation_line.update(data)


class VariantBuilder(object):
    def __init__(self, config, genome):
        assert isinstance(config, VariantAnnotatorConfig)
        self.config = config
        self.genome = genome

    def build_variant(self, annotation_line):
        raise NotImplementedError()

    def build(self, annotation_line):
        summary = self.build_variant(annotation_line)
        if summary is None:
            data = {
                'CSHL:location': None,
                'CSHL:chr': None,
                'CSHL:position': None,
                'CSHL:variant': None,
                'VCF:chr': None,
                'VCF:position': None,
                'VCF:ref': None,
                'VCF:alt': None,
            }
        else:
            data = {
                'CSHL:location': summary.cshl_location,
                'CSHL:chr': summary.chromosome,
                'CSHL:position': summary.cshl_position,
                'CSHL:variant': summary.cshl_variant,
                'VCF:chr': summary.chromosome,
                'VCF:position': summary.position,
                'VCF:ref': summary.reference,
                'VCF:alt': summary.alternative,
            }
        annotation_line.update(data)
        return summary


class DAEBuilder(VariantBuilder):

    def __init__(self, config, genome):
        super(DAEBuilder, self).__init__(config, genome)
        self.variant = self.config.options.v
        self.chrom = self.config.options.c
        self.position = self.config.options.p
        self.location = self.config.options.x
        if self.variant is None:
            self.variant = "variant"
        if self.location is None:
            self.location = "location"
        if self.chrom is None:
            self.chrom = "chr"
        if self.position is None:
            self.position = "position"

    def build_variant(self, aline):
        variant = aline[self.variant]
        if self.location in aline:
            location = aline[self.location]
            chrom, position = location.split(':')
        else:
            assert self.chrom in aline
            assert self.position in aline
            chrom = aline[self.chrom]
            position = aline[self.position]

        vcf_position, ref, alt = dae2vcf_variant(
            chrom, int(position), variant, self.genome
        )
        summary = SummaryAllele(chrom, vcf_position, ref, alt)
        return summary


class VCFBuilder(VariantBuilder):

    def __init__(self, config, genome):
        super(VCFBuilder, self).__init__(config, genome)
        self.chrom = self.config.options.c
        self.position = self.config.options.p
        self.ref = self.config.options.r
        self.alt = self.config.options.a

    def build_variant(self, aline):
        chrom = aline[self.chrom]
        position = aline[self.position]
        ref = aline[self.ref]
        alt = aline[self.alt]

        if chrom is None or position is None:
            return None
        if not alt:
            return None

        summary = SummaryAllele(
            chrom, int(position), ref, alt
        )
        return summary


class VariantAnnotatorBase(AnnotatorBase):

    def __init__(self, config):
        super(VariantAnnotatorBase, self).__init__(config)

        assert isinstance(config, VariantAnnotatorConfig)

        self.genome = None

        if self.config.options.vcf:
            self.variant_builder = VCFBuilder(self.config, self.genome)
        else:
            self.genome = GenomeAccess.openRef(self.config.genome_file)
            assert self.genome is not None
            self.variant_builder = DAEBuilder(self.config, self.genome)

        if not self.config.virtual_columns:
            self.config.virtual_columns = [
                'CSHL:location',
                'CSHL:chr',
                'CSHL:position',
                'CSHL:variant',
                'VCF:chr',
                'VCF:position',
                'VCF:ref',
                'VCF:alt',
            ]

    def collect_annotator_schema(self, schema):
        for vcol in self.config.virtual_columns:
            if 'position' in vcol:
                schema.create_column(vcol, 'int')
            else:
                schema.create_column(vcol, 'str')

    def line_annotation(self, aline):
        variant = self.variant_builder.build(aline)
        self.do_annotate(aline, variant)

    def do_annotate(self, aline, variant):
        raise NotImplementedError()


class CompositeAnnotator(AnnotatorBase):

    def __init__(self, config):
        super(CompositeAnnotator, self).__init__(config)
        self.annotators = []

    def add_annotator(self, annotator):
        assert isinstance(annotator, AnnotatorBase)
        self.annotators.append(annotator)

    def line_annotation(self, aline):
        for annotator in self.annotators:
            annotator.line_annotation(aline)

    def collect_annotator_schema(self, schema):
        for annotator in self.annotators:
            annotator.collect_annotator_schema(schema)


class CompositeVariantAnnotator(VariantAnnotatorBase):

    def __init__(self, config):
        super(CompositeVariantAnnotator, self).__init__(config)
        self.annotators = []

    def add_annotator(self, annotator):
        assert isinstance(annotator, VariantAnnotatorBase)
        self.annotators.append(annotator)

    def line_annotation(self, aline):
        variant = self.variant_builder.build(aline)
        for annotator in self.annotators:
            annotator.do_annotate(aline, variant)

    def collect_annotator_schema(self, schema):
        super(CompositeVariantAnnotator, self).collect_annotator_schema(schema)
        for annotator in self.annotators:
            annotator.collect_annotator_schema(schema)
