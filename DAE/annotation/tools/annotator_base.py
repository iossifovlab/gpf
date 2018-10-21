from ast import literal_eval
from box import Box
import common.config
from configparser import ConfigParser
import re
from collections import OrderedDict
from importlib import import_module
from annotation.tools.annotator_config import LineConfig, Line, \
    AnnotatorConfig, \
    VariantAnnotatorConfig
from utils.dae_utils import dae2vcf_variant
from variants.variant import SummaryAllele
import GenomeAccess


class HeaderSection(object):

    def __init__(self, input_columns, output_columns):
        self.name = "Header"
        self.inpupt_columns = input_columns[:]
        self.output_columns = output_columns[:]


class AnnotationSection(object):

    def __init__(
            self, section_name, annotator_name, options, columns, virtuals):
        self.name = section_name
        self.annotator_name = annotator_name
        self.options = options
        self.columns = columns
        self.input_columns = list(columns.values())
        self.native_columns = list(columns.keys())
        self.virtual_columns = list(virtuals)
        assert all([c in self.input_columns for c in self.virtual_columns])

        self.output_columns = [
            c for c in self.input_columns if c not in self.virtual_columns
        ]

    @staticmethod
    def _split_class_name(class_fullname):
        splitted = class_fullname.split('.')
        module_path = splitted[:-1]
        assert len(module_path) >= 1
        if len(module_path) == 1:
            module_path = ["annotation", "tools", *module_path]

        module_name = '.'.join(module_path)
        class_name = splitted[-1]

        return module_name, class_name

    @staticmethod
    def _name_to_class(class_fullname):
        module_name, class_name = \
            AnnotationSection._split_class_name(class_fullname)
        module = import_module(module_name)
        clazz = getattr(module, class_name)
        return clazz

    @staticmethod
    def instantiate(section):
        clazz = AnnotationSection._name_to_class(section.annotator_name)
        assert clazz is not None
        return clazz(section.options, section)


class AnnotationConfig(object):

    def __init__(self):
        self.default_options = {}
        self.configuration = Box({})

        self.mode = "replace"
        self.header_section = None
        self.annotation_sections = []

    @staticmethod
    def build(args, conf_file, input_header):
        default_options = AnnotationConfig._parse_default_options(
            args.default_arguments
        )
        default_options['region'] = args.region
        default_options = Box(
            default_options, 
            default_box=True, default_box_attr=None)
        configuration = AnnotationConfig._parse_annotation_config(
            conf_file
        )
        result = AnnotationConfig()
        result.default_options = default_options
        result.configuration = configuration
        result.mode = "replace"

        result._set_input_header(input_header)

        for section_name, section_config in configuration.items():
            section = result._parse_annotation_section(
                section_name, section_config)
            result._append_annotation_section(section)
        return result

    def _append_annotation_section(self, section):
        self.annotation_sections.append(section)

    def _set_input_header(self, header):
        if self.mode != "overwrite":
            self.header_section = HeaderSection(header, header)
        else:
            self.header_section = HeaderSection(header, [])
        self.annotation_sections.append(self.header_section)

    @staticmethod
    def _parse_default_options(default_options):
        extracted_options = []
        if default_options is not None:
            for option in default_options.split(','):
                split_options = option.split(':')
                try:
                    split_options[1] = literal_eval(split_options[1])
                except ValueError:
                    pass
                extracted_options.append(split_options)
        return dict(extracted_options)

    @staticmethod
    def _parse_annotation_config(filename):
        class AnnotationConfigParser(ConfigParser):
            """Modified ConfigParser.SafeConfigParser that
            allows ':' in keys and only '=' as separator.
            """
            OPTCRE = re.compile(
                r'(?P<option>[^=\s][^=]*)'          # allow only =
                r'\s*(?P<vi>[=])\s*'                # for option separator
                r'(?P<value>.*)$'
                )

        config_parser = AnnotationConfigParser()
        config_parser.optionxform = str
        with open(filename, "r", encoding="utf8") as infile:
            config_parser.read_file(infile)
            config = Box(
                common.config.to_dict(config_parser),
                default_box=True, default_box_attr=None)
        return config

    def _parse_annotation_section(self, section_name, section):
        assert section.annotator is not None
        annotator_name = section.annotator
        options = dict(self.default_options)
        for key, val in section.options.items():
            try:
                val = literal_eval(val)
            except Exception:
                pass
            options[key] = val

        columns = OrderedDict(section.columns)
        if section.virtuals is None:
            virtuals = []
        else:
            virtuals = [
                c.strip() for c in section.virtuals.split(',')
            ]
        return AnnotationSection(
            section_name=section_name,
            annotator_name=annotator_name,
            options=options,
            columns=columns,
            virtuals=virtuals
        )

    def output_length(self):
        return sum([
            len(section.output_columns) for section in self.annotation_sections
        ])


class AnnotatorBase(object):

    """
    `AnnotatorBase` is base class of all `Annotators` and `Preannotators`.
    """

    def __init__(self, config):
        assert isinstance(config, AnnotatorConfig)

        self.config = config

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
        summary = SummaryAllele(vcf_position, ref, alt)
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

        if self.config.mode == "VCF":
            self.variant_builder = VCFBuilder(self.config, self.genome)
        elif self.config.mode == "DAE":
            self.variant_builder = DAEBuilder(self.config, self.genome)
            self.genome = GenomeAccess.openRef(self.config.genome_file)
        else:
            raise ValueError(self.config.mode)

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