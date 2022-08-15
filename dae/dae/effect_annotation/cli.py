import sys
import logging
import gzip
from argparse import ArgumentParser
from typing import Dict, Iterator, List, Optional, Tuple

from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.genomic_context import GenomicContext
from dae.genomic_resources.genomic_context import get_genomic_context
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.gene_models import GeneModels, \
    build_gene_models_from_file, \
    build_gene_models_from_resource
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.reference_genome import \
    build_reference_genome_from_file
from dae.genomic_resources.reference_genome import \
    build_reference_genome_from_resource

from dae.effect_annotation.annotator import EffectAnnotator
from dae.effect_annotation.effect import AnnotationEffect

logger = logging.getLogger(__name__)


class EffectAnnotatorBuilder:
    @staticmethod
    def set_arguments(parser: ArgumentParser) -> None:
        genomic_repository_group = parser.add_argument_group(
            "Genomic repository options")

        genomic_repository_group.add_argument(
            "-grr", "--genomic-repository-config-filename",
            help="Genomic Repository Configuraiton File"
        )

        gene_model_file_group = parser.add_argument_group(
            "Gene models file options")

        gene_model_file_group.add_argument(
            "-gmfn", "--gene-models-filename",
            help="Gene models file name."
        )
        gene_model_file_group.add_argument(
            "-gmff", "--gene-models-fileformat",
            help="Gene models file format."
        )
        gene_model_file_group.add_argument(
            "-gmmfn", "--gene-mapping-filename",
            help="Gene mapping file.",
            default=None,
            action="store",
        )
        gene_model_resource_group = parser.add_argument_group(
            "Gene models resource options")
        gene_model_resource_group.add_argument(
            "-gmri", "--gene-models-resource-id",
            help="Gene models resource id."
        )

        reference_genome_file_group = parser.add_argument_group(
            "Reference genome file options")
        reference_genome_file_group.add_argument(
            "-rgfn", "--reference-genome-filename",
            help="Reference genome file name."
        )

        reference_genome_resource_group = parser.add_argument_group(
            "Reference genome resource options")
        reference_genome_resource_group.add_argument(
            "-rgri", "--reference-genome-resource-id",
            help="Reference genome resource id."
        )

        parser.add_argument(
            "-pl", "--promoter-len",
            help="promoter length",
            default=0,
            type=int,
        )

    def __init__(self, args):
        self.args = args
        self._gc: Optional[GenomicContext] = None

    def get_genomic_context(self) -> GenomicContext:
        if not self._gc:
            self._gc = get_genomic_context()
        return self._gc

    def get_grr(self) -> GenomicResourceRepo:
        grr: Optional[GenomicResourceRepo] = None

        if self.args.genomic_repository_config_filename:
            grr = build_genomic_resource_repository(
                self.args.genomic_repository_config_filename)
        else:
            grr = self.get_genomic_context().get_genomic_resources_repository()
        if grr:
            return grr
        return build_genomic_resource_repository()

    def get_gene_models(self) -> GeneModels:
        if self.args.gene_models_resource_id:
            resource = self.get_grr().get_resource(
                self.args.gene_models_resource_id)
            return build_gene_models_from_resource(resource)

        if self.args.gene_models_filename:
            return build_gene_models_from_file(
                self.args.gene_models_filename,
                self.args.gene_models_fileformat,
                self.args.gene_mapping_filename)

        gm = self.get_genomic_context().get_gene_models()
        if gm:
            return gm
        raise Exception("No gene models could be found!")

    def get_refernce_genome(self) -> ReferenceGenome:
        if self.args.reference_genome_resource_id:
            resource = self.get_grr().get_resource(
                self.args.reference_genome_resource_id)
            return build_reference_genome_from_resource(resource)

        if self.args.reference_genome_filename:
            return build_reference_genome_from_file(
                self.args.reference_genome_filename)

        ref = self.get_genomic_context().get_reference_genome()
        if ref:
            return ref
        raise Exception("No reference genome could be found!")

    def build_effect_annotator(self):
        ref = self.get_refernce_genome()
        gm = self.get_gene_models()
        logger.info(
            "Building effect annotator with:\n"
            "\treferende genome from %s,\n"
            "\tgene models from %s, and\n"
            "\tpromoter lengths of %s",
            ref.resource.resource_id, gm.resource.resource_id,
            self.args.promoter_len)
        return EffectAnnotator(ref, gm, promoter_len=self.args.promoter_len)


class VariantColumnInputFile:
    variant_columns = ["chrom", "pos",
                       "location", "variant", "ref", "alt"]

    @staticmethod
    def set_argument(parser: ArgumentParser):
        variant_columns_group = parser.add_argument_group(
            "Variant columns")
        for vc in VariantColumnInputFile.variant_columns:
            variant_columns_group.add_argument(
                f"--{vc}-col",
                default=vc)
        input_file_group = parser.add_argument_group(
            "Input file")
        input_file_group.add_argument("input_filename",
                                      nargs='?', default="-")
        input_file_group.add_argument("--input-sep", default="\t")

    def __init__(self, args):
        self.args = args

        # open file
        filename = self.args.input_filename
        if filename == "-":
            self.file = sys.stdin
        else:
            if filename.endswith("gz"):
                self.file = gzip.open(filename, "rt")
            else:
                self.file = open(filename, "rt")

        # read header
        self.header: List[str] = self.file.readline(). \
            strip("\n\r").split(self.args.input_sep)

        # prepare the variant_attribute_index
        args_dict = vars(self.args)
        self.variant_attribute_index: Dict[str, int] = {}
        for variant_attribute in VariantColumnInputFile.variant_columns:
            col = args_dict[f'{variant_attribute}_col']
            idx = [i for i, h in enumerate(self.header) if h == col]
            if len(idx) > 1:
                raise Exception(f"the column {col} is repeated twice in the "
                                f"input file {filename}")
            if len(idx) == 1:
                self.variant_attribute_index[variant_attribute] = idx[0]

    def get_header(self) -> List[str]:
        return self.header

    def get_lines(self) -> Iterator[Tuple[List[str], Dict[str, str]]]:
        for line in self.file:
            cs = line.strip("\n\r").split(self.args.input_sep)
            variant_attributes = \
                {k: cs[i] for k, i in self.variant_attribute_index.items()}
            yield cs, variant_attributes

    def close(self) -> None:
        self.file.close()


class VariantColumnOutputFile:
    @staticmethod
    def set_argument(parser: ArgumentParser):
        output_file_group = parser.add_argument_group(
            "Output file")
        output_file_group.add_argument("output_filename",
                                       nargs='?', default="-")
        output_file_group.add_argument("--output-sep", default="\t")

    def __init__(self, args):
        self.args = args

        filename = self.args.output_filename
        if filename == "-":
            self.file = sys.stdout
        else:
            if filename.endswith("gz"):
                self.file = gzip.open(filename, "wt")
            else:
                self.file = open(filename, "wt")

    def write_columns(self, cs) -> None:
        print(*cs, sep=self.args.output_sep, file=self.file)

    def close(self) -> None:
        self.file.close()


class AnnotationAttributes:
    ALL_ATTRIBUTE_IDXS = {aa: aai for aai, aa in enumerate(
        ["worst_effect", "gene_effects", "effect_details"])}

    @staticmethod
    def set_argument(parser: ArgumentParser, default_columns: str =
                     "worst_effect,gene_effects,effect_details"):
        annotation_attributes_group = parser.add_argument_group(
            'Annotation attributes.')
        annotation_attributes_group. \
            add_argument("--annotation-attributes",
                         default=default_columns,
                         help="The available attributes are "
                         "worst_effect, gene_effects, and effect_details. "
                         "Examples: "
                         "1. 'worst_effect, gene_effects';"
                         "2. 'WE: worst_effect, GE: gene_effects, "
                         "ED: effect_details'"
                         f"The default is : '{default_columns}'.")

    def __init__(self, args):
        self.args = args
        self.out_attributes: List[str] = []
        self.source_attributes: List[str] = []

        for attribute_def in self.args.annotation_attributes.split(","):
            parts = attribute_def.split(":")
            if len(parts) == 1:
                out = parts[0]
                source = parts[0]
            elif len(parts) == 2:
                out = parts[0]
                source = parts[1]
            else:
                raise Exception("In correct attribute definition. "
                                "TO IMPROVE MESSAGE!")
            self.out_attributes.append(out)
            self.source_attributes.append(source)
        if len(self.out_attributes) != len(set(self.out_attributes)):
            raise Exception("The output attributes should not be repeated. "
                            "TO IMPROVE MESSAGE!!!")
        self.value_idxs = [AnnotationAttributes.ALL_ATTRIBUTE_IDXS[aa]
                           for aa in self.source_attributes]

    def get_out_attributes(self) -> List[str]:
        return self.out_attributes

    def get_source_attributes(self) -> List[str]:
        return self.source_attributes

    def get_values(self, E) -> List[str]:
        full_desc = AnnotationEffect.effects_description(E)
        return [full_desc[idx] for idx in self.value_idxs]


def cli_columns():
    parser = ArgumentParser(
        description="Annotate Variant Effects in a Column File.")

    VerbosityConfiguration.set_argumnets(parser)
    EffectAnnotatorBuilder.set_arguments(parser)
    VariantColumnInputFile.set_argument(parser)
    VariantColumnOutputFile.set_argument(parser)
    AnnotationAttributes.set_argument(parser)

    args = parser.parse_args(sys.argv[1:])
    VerbosityConfiguration.set(args)
    annotator = EffectAnnotatorBuilder(args).build_effect_annotator()
    input_file = VariantColumnInputFile(args)
    output_file = VariantColumnOutputFile(args)
    annotation_attributes = AnnotationAttributes(args)

    output_file.write_columns(
        input_file.get_header() + annotation_attributes.get_out_attributes())
    for cs, vdef in input_file.get_lines():
        logger.debug("vdef: %s AAA", vdef)
        E = annotator.do_annotate_variant(**vdef)
        output_file.write_columns(cs + annotation_attributes.get_values(E))


def cli_vcf():
    import pysam  # type: ignore

    parser = ArgumentParser(
        description="Annotate Variant Effects in a VCF file.")

    VerbosityConfiguration.set_argumnets(parser)
    EffectAnnotatorBuilder.set_arguments(parser)
    AnnotationAttributes.set_argument(
        parser,
        default_columns="WE:worst_effect,GE:gene_effects,ED:effect_details")

    parser.add_argument("input_filename", help="input VCF variants file name")
    parser.add_argument(
        "output_filename", nargs="?", help="output file name (default: stdout)"
    )
    args = parser.parse_args(sys.argv[1:])
    VerbosityConfiguration.set(args)
    annotator = EffectAnnotatorBuilder(args).build_effect_annotator()
    annotation_attributes = AnnotationAttributes(args)

    # pylint: disable=no-member
    infile = pysam.VariantFile(args.input_filename)
    if args.output_filename is None:
        outfile = sys.stdout
    else:
        outfile = open(args.output_filename, "w")

    # handling the header
    header = infile.header
    header.add_meta(
        "variant_effect_annotation", "GPF variant effects annotation."
    )
    header.add_meta(
        "variant_effect_annotation_command", '"{}"'.format(" ".join(sys.argv))
    )
    source_attribute_description = {
        "worst_effect": "The worst effect.",
        "gene_effects": "Gene effects.",
        "effect_details": "Detailed effects."
    }
    for out_a, src_a in zip(annotation_attributes.get_out_attributes(),
                            annotation_attributes.get_source_attributes()):
        header.info.add(out_a, "A", "String",
                        source_attribute_description[src_a])

    print(str(header), file=outfile, end="")

    # handling the variants
    out_as = annotation_attributes.get_out_attributes()
    for variant in infile:
        buffers = [list([]) for _ in out_as]

        for alt in variant.alts:
            E = annotator.do_annotate_variant(
                chrom=variant.chrom,
                pos=variant.pos,
                ref=variant.ref,
                alt=alt
            )
            for buff, v in zip(buffers, annotation_attributes.get_values(E)):
                buff.append(v)

        for out_a, buff in zip(out_as, buffers):
            variant.info[out_a] = ",".join(buff)
        print(str(variant), file=outfile, end="")

    infile.close()
    if args.output_filename:
        outfile.close()


if __name__ == "__main__":
    cli_columns()
