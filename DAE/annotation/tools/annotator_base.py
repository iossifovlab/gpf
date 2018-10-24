
from annotation.tools.annotator_config import LineConfig, Line, \
    AnnotatorConfig, \
    VariantAnnotatorConfig
from utils.dae_utils import dae2vcf_variant
from variants.variant import SummaryAllele
import GenomeAccess


class AnnotatorBase(object):

    """
    `AnnotatorBase` is base class of all `Annotators` and `Preannotators`.
    """

    def __init__(self, config):
        assert isinstance(config, AnnotatorConfig)

        self.config = config

        self.mode = "overwrite"
        if self.config.options.mode == "replace":
            self.mode = "replace"

    def build_ouput_line(self, annotation_line):
        output_columns = self.config.output_columns
        return [
            annotation_line.columns.get(key, '') for key in output_columns
        ]

    def annotate_file(self, file_io_manager):
        """
            Method for annotating file from `Annotator`.
        """
        line_config = LineConfig(file_io_manager.header)
        if self.mode == 'replace':
            output_columns = file_io_manager.header
            extended = [
                col for col in self.config.output_columns
                if col not in output_columns]
            output_columns.extend(extended)
            self.config.output_columns = output_columns

        file_io_manager.line_write(self.config.output_columns)

        for line in file_io_manager.lines_read():
            if '#' in line[0]:
                file_io_manager.line_write(line)
                continue
            annotation_line = line_config.build(line)
            self.line_annotation(annotation_line)

            file_io_manager.line_write(
                self.build_ouput_line(annotation_line))

    def line_annotation(self, annotation_line, variant=None):
        """
            Method returning annotations for the given line
            in the order from new_columns parameter.
        """
        raise NotImplementedError()


class CopyAnnotator(AnnotatorBase):

    def __init__(self, config):
        super(CopyAnnotator, self).__init__(config)

    def line_annotation(self, annotation_line, variant=None):
        data = {}
        for key, value in self.config.columns_config.items():
            data[value] = annotation_line.columns[key]
        annotation_line.columns.update(data)


class VariantBuilder(object):
    def __init__(self, config, genome):
        assert isinstance(config, VariantAnnotatorConfig)
        self.config = config
        self.genome = genome

    def build_variant(self, annotation_line):
        raise NotImplementedError()

    def build(self, annotation_line):
        # import pdb; pdb.set_trace()
        summary = self.build_variant(annotation_line)

        data = {
            'CSHL:location': summary.details.cshl_location,
            'CSHL:chr': summary.chromosome,
            'CSHL:position': summary.details.cshl_position,
            'CSHL:variant': summary.details.cshl_variant,
            'VCF:chr': summary.chromosome,
            'VCF:position': summary.position,
            'VCF:ref': summary.reference,
            'VCF:alt': summary.alternative,
        }
        annotation_line.columns.update(data)
        return summary


class DAEBuilder(VariantBuilder):

    def __init__(self, config, genome):
        super(DAEBuilder, self).__init__(config, genome)
        self.variant = self.config.options.v
        self.chrom = self.config.options.c
        self.position = self.config.options.p
        self.location = self.config.options.x

    def build_variant(self, aline):
        variant = aline.columns[self.variant]
        if self.location:
            location = aline.columns[self.location]
            chrom, position = location.split(':')
        else:
            assert self.chrom is not None
            assert self.position is not None
            chrom = aline.columns[self.chrom]
            position = aline.columns[self.position]
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
        chrom = aline.columns[self.chrom]
        position = aline.columns[self.position]
        ref = aline.columns[self.ref]
        alt = aline.columns[self.alt]

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

    def annotate_file(self, file_io_manager):
        """
            Method for annotating file from `Annotator`.
        """
        line_config = LineConfig(file_io_manager.header)
        if self.mode == 'replace':
            output_columns = file_io_manager.header
            extended = [
                col for col in self.config.output_columns
                if col not in output_columns]
            output_columns.extend(extended)
            self.config.output_columns = output_columns

        file_io_manager.line_write(self.config.output_columns)

        for line in file_io_manager.lines_read():
            if '#' in line[0]:
                file_io_manager.line_write(line)
                continue
            annotation_line = line_config.build(line)
            variant = self.variant_builder.build(annotation_line)

            self.line_annotation(annotation_line, variant=variant)

            file_io_manager.line_write(
                self.build_ouput_line(annotation_line))


class CompositeVariantAnnotator(VariantAnnotatorBase):

    def __init__(self, config):
        super(CompositeVariantAnnotator, self).__init__(config)
        self.annotators = []

    def add_annotator(self, annotator):
        assert isinstance(annotator, AnnotatorBase)
        self.annotators.append(annotator)

    def line_annotation(self, aline, variant=None):
        assert variant is not None
        assert isinstance(aline, Line)

        for annotator in self.annotators:
            annotator.line_annotation(aline, variant)
