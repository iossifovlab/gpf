import sys
import logging
import gzip
from argparse import ArgumentParser
from typing import Dict, Iterator, List, Optional, Tuple, cast

from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.genomic_context import GenomicContext
from dae.genomic_resources.genomic_context import get_genomic_context
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.gene_models import load_gene_models
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.reference_genome import open_ref
from dae.genomic_resources.gene_models_resource import GeneModelsResource
from dae.genomic_resources.reference_genome_resource import \
    ReferenceGenomeResource

from dae.effect_annotation.annotator import EffectAnnotator
from dae.effect_annotation.effect import AnnotationEffect

logger = logging.getLogger(__name__)


class EffectAnnotatorBuilder:
    @staticmethod
    def set_arguments(parser: ArgumentParser) -> None:
        gene_model_file_group = parser.add_argument_group(
            "Gene models file options")

        gene_model_file_group.add_argument(
            "--gene-models-filename",
            help="Gene models file name."
        )
        gene_model_file_group.add_argument(
            "--gene-models-fileformat",
            help="Gene models file format."
        )
        gene_model_file_group.add_argument(
            "--gene-mapping-filename",
            help="Gene mapping file.",
            default=None,
            action="store",
        )
        gene_model_resource_group = parser.add_argument_group(
            "Gene models resource options")
        gene_model_resource_group.add_argument(
            "--gene-models-resource-id",
            help="Gene models resource id."
        )

        reference_genome_file_group = parser.add_argument_group(
            "Reference genome file options")
        reference_genome_file_group.add_argument(
            "--reference-genome-filename",
            help="Reference genome file name."
        )

        reference_genome_resource_group = parser.add_argument_group(
            "Reference genome resource options")
        reference_genome_resource_group.add_argument(
            "--reference-genome-resource-id",
            help="Reference genome resource id."
        )

        parser.add_argument(
            "--promoter-len",
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
        grr = self.get_genomic_context().get_genomic_resource_repository()
        if grr:
            return grr
        return build_genomic_resource_repository()

    def get_gene_models(self) -> GeneModels:
        if self.args.gene_models_resource_id:
            resource = self.get_grr().get_resource(
                self.args.gene_models_resource_id)
            if not isinstance(resource, GeneModelsResource):
                raise Exception("The resoruce with id "
                                f"{self.args.gene_models_resource_id} is not "
                                "a GeneModels resoruce.")
            gm_resource = cast(GeneModelsResource, resource)
            return gm_resource.open()

        if self.args.gene_models_filename:
            return load_gene_models(self.args.gene_models_filename,
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
            if not isinstance(resource, ReferenceGenomeResource):
                raise Exception("The resoruce with id "
                                f"{self.args.reference_genome_resource_id} is "
                                "not a ReferenceGenome resource.")
            rg_resource = cast(ReferenceGenomeResource, resource)
            return rg_resource.open()

        if self.args.reference_genome_filename:
            return open_ref(self.args.reference_genome_filename)

        ref = self.get_genomic_context().get_reference_genome()
        if ref:
            return ref
        raise Exception("No reference genome could be found!")

    def build_effect_annotator(self):
        ref = self.get_refernce_genome()
        gm = self.get_gene_models()
        logger.info(f"Building effect annotator with:\n"
                    f"\treferende genome from {ref.source},\n"
                    f"\tgene models from {gm.source}, and\n"
                    f"\tpromoter lengths of {self.args.promoter_len}")
        return EffectAnnotator(ref, gm, promoter_len=self.args.promoter_len)


def set_verbosity_argumnets(parser: ArgumentParser) -> None:
    parser.add_argument('--verbose', '-V', action='count', default=0)


def set_verbosity(args):
    if args.verbose == 1:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose >= 2:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)


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
        self.header = self.file.readline(). \
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
    def set_argument(parser: ArgumentParser):
        annotation_attributes_group = parser.add_argument_group(
            "Annotation attributes")
        annotation_attributes_group. \
            add_argument("--annotation-attributes",
                         default="worst_effect,gene_effects,effect_details")

    def __init__(self, args):
        self.args = args
        self.attributes = self.args.annotation_attributes.split(",")
        self.value_idxs = [AnnotationAttributes.ALL_ATTRIBUTE_IDXS[aa]
                           for aa in self.attributes]

    def get_attributes(self) -> List[str]:
        return self.attributes

    def get_values(self, E) -> List[str]:
        full_desc = AnnotationEffect.effects_description(E)
        return [full_desc[idx] for idx in self.value_idxs]


def cli_columns():
    parser = ArgumentParser(
        description="Annotate Variant Effects in a Column File.")

    set_verbosity_argumnets(parser)
    EffectAnnotatorBuilder.set_arguments(parser)
    VariantColumnInputFile.set_argument(parser)
    VariantColumnOutputFile.set_argument(parser)
    AnnotationAttributes.set_argument(parser)

    args = parser.parse_args(sys.argv[1:])
    set_verbosity(args)
    annotator = EffectAnnotatorBuilder(args).build_effect_annotator()
    input_file = VariantColumnInputFile(args)
    output_file = VariantColumnOutputFile(args)
    annotation_attributes = AnnotationAttributes(args)

    output_file.write_columns(
        input_file.get_header() + annotation_attributes.get_attributes())
    for cs, vdef in input_file.get_lines():
        E = annotator.do_annotate_variant(**vdef)
        output_file.write_columns(cs + annotation_attributes.get_values(E))


def cli_vcf():
    pass


if __name__ == "__main__":
    cli_columns()
