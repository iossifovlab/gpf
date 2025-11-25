import abc
import argparse
import logging
import pathlib
import sys
import textwrap
from typing import cast

from dae.annotation.annotatable import (
    CNVAllele,
    VCFAllele,
)
from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.genomic_resources.genomic_context import (
    context_providers_add_argparser_arguments,
    context_providers_init,
    get_genomic_context,
)
from dae.genomic_resources.reference_genome import (
    ReferenceGenome,
    build_reference_genome_from_resource,
)
from dae.genomic_resources.repository_factory import (
    GenomicResourceRepo,
)
from dae.pedigrees.loader import FamiliesLoader
from dae.utils.regions import Region
from dae.utils.variant_utils import mat2str
from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.variants.family_variant import FamilyAllele
from dae.variants.variant import VariantDetails
from dae.variants_loaders.cnv.loader import CNVLoader
from dae.variants_loaders.dae.loader import (
    DaeTransmittedLoader,
    DenovoLoader,
)
from dae.variants_loaders.raw.loader import VariantsGenotypesLoader

logger = logging.getLogger("cnv_liftover")


def _build_variant_loader(
    loader_class: type[VariantsGenotypesLoader],
    args: argparse.Namespace,
    source_genome: ReferenceGenome,
) -> VariantsGenotypesLoader:
    families_filenames, families_params = \
        FamiliesLoader.parse_cli_arguments(args)
    families_filename = families_filenames[0]

    families_loader = FamiliesLoader(
        families_filename, **families_params,
    )
    families = families_loader.load()

    variants_filenames, variants_params = \
        loader_class.parse_cli_arguments(args)

    return loader_class(
        families,
        variants_filenames,
        params=variants_params,
        genome=source_genome,
    )


def _region_output_filename(
    output_filename: str,
    region: Region | None,
) -> str:
    if region is None:
        return output_filename
    out = pathlib.Path(output_filename)
    suffixes = out.suffixes
    output_prefix = out
    for _ in suffixes:
        output_prefix = output_prefix.with_suffix("")

    region_str = str(region).replace(":", "_").replace("-", "_")
    suffix = "".join(suffixes)
    return f"{output_prefix}_{region_str}{suffix}"


def _liftover_denovo_variants(
    output_filename: str,
    variants_loader: VariantsGenotypesLoader,
    pipeline: AnnotationPipeline,
    region: Region | None = None,
) -> None:
    assert isinstance(variants_loader, DenovoLoader)

    if region is not None:
        logger.info("resetting regions (region): %s", region)
        variants_loader.reset_regions([region])
        output_filename = _region_output_filename(output_filename, region)

    logger.info("output: %s", output_filename)

    with open(output_filename, "wt") as output:

        header = [
            "chrom", "pos", "ref", "alt",  # target variant
            "chrom_src", "pos_src", "ref_src", "alt_src",  # source variant
            "familyId", "bestSt",
        ]

        additional_columns = set(variants_loader.denovo_df.columns) - {
            "chrom", "position", "reference", "alternative", "family_id",
            "genotype", "best_state",
        }
        header.extend(sorted(additional_columns))

        output.write("\t".join(header))
        output.write("\n")

        for sv, fvs in variants_loader.full_variants_iterator():
            assert len(sv.alt_alleles) == 1

            aa = sv.alt_alleles[0]
            annotatable: VCFAllele = cast(VCFAllele, aa.get_annotatable())
            result = pipeline.annotate(annotatable)
            liftover_annotatable: VCFAllele = \
                cast(VCFAllele, result.get("target_annotatable"))

            if liftover_annotatable is None:
                logger.error("can't liftover %s", aa)
                continue

            for fv in fvs:
                fa = cast(FamilyAllele, fv.alt_alleles[0])

                line = [
                    liftover_annotatable.chrom,
                    str(liftover_annotatable.pos),
                    liftover_annotatable.ref,
                    liftover_annotatable.alt,

                    annotatable.chrom, str(annotatable.pos),
                    annotatable.ref, annotatable.alt,

                    fa.family_id,
                    mat2str(fa.best_state, col_sep=" "),
                ]
                line.extend([
                    str(fa.get_attribute(col) or "")
                    for col in sorted(additional_columns)])
                output.write("\t".join(line))
                output.write("\n")


def _liftover_cnv_variants(
    output_filename: str,
    variants_loader: VariantsGenotypesLoader,
    pipeline: AnnotationPipeline,
    region: Region | None = None,
) -> None:
    assert isinstance(variants_loader, CNVLoader)

    if region is not None:
        logger.info("resetting regions (region): %s", region)
        variants_loader.reset_regions([region])
        output_filename = _region_output_filename(output_filename, region)

    logger.info("output: %s", output_filename)
    with open(output_filename, "wt") as output:
        header = [
            "location", "cnv_type",
            "location_src", "cnv_type_src",
            "size_change",
            "familyId", "personId",
        ]

        output.write("\t".join(header))
        output.write("\n")

        for sv, fvs in variants_loader.full_variants_iterator():
            assert len(sv.alt_alleles) == 1

            aa = sv.alt_alleles[0]
            annotatable: CNVAllele = cast(CNVAllele, aa.get_annotatable())
            result = pipeline.annotate(annotatable)
            liftover_annotatable: CNVAllele = \
                cast(CNVAllele, result.get("target_annotatable"))

            if liftover_annotatable is None:
                logger.error("can't liftover %s", aa)
                continue

            for fv in fvs:
                size_src = len(annotatable)
                size = len(liftover_annotatable)

                size_diff = (100.0 * abs(size_src - size)) / size_src
                if size_diff >= 50:
                    logger.warning(
                        "CNV variant size changed more than 50 percent: %s; "
                        "%s -> %s",
                        size_diff, annotatable, liftover_annotatable)

                for aa in fv.alt_alleles:
                    fa = cast(FamilyAllele, aa)
                    line: list[str] = []
                    person_ids = [
                        person_id
                        for person_id in fa.variant_in_members
                        if person_id is not None
                    ]
                    assert len(person_ids) >= 1
                    line = [
                        f"{liftover_annotatable.chrom}:"
                        f"{liftover_annotatable.pos}-"
                        f"{liftover_annotatable.pos_end}",
                        liftover_annotatable.type.name,
                        f"{annotatable.chrom}:"
                        f"{annotatable.pos}-"
                        f"{annotatable.pos_end}",
                        annotatable.type.name,
                        str(size_diff),
                        fa.family_id,
                        ";".join(person_ids),
                    ]

                    output.write("\t".join(line))
                    output.write("\n")


def _liftover_dae_variants(
    output_prefix: str,
    variants_loader: VariantsGenotypesLoader,
    pipeline: AnnotationPipeline,
    region: Region | None = None,
) -> None:
    assert isinstance(variants_loader, DaeTransmittedLoader)

    summary_filename = f"{output_prefix}.txt"
    toomany_filename = f"{output_prefix}-TOOMANY.txt"
    if region is not None:
        logger.info("resetting regions (region): %s", region)
        variants_loader.reset_regions([region])
        summary_filename = f"{output_prefix}-{region}.txt"
        toomany_filename = f"{output_prefix}-TOOMANY-{region}.txt"
    logger.info("summary output: %s", summary_filename)
    logger.info("toomany output: %s", toomany_filename)

    with open(summary_filename, "wt") as output_summary, \
            open(toomany_filename, "wt") as output_toomany:

        summary_header = [
            "#chr", "position", "variant",
            "familyData",
            "all.nParCalled", "all.prcntParCalled",
            "all.nAltAlls", "all.altFreq",
        ]
        toomany_header = [
            "#chr", "position", "variant",
            "familyData",
        ]

        output_summary.write("\t".join(summary_header))
        output_summary.write("\n")

        output_toomany.write("\t".join(toomany_header))
        output_toomany.write("\n")

        for sv, fvs in variants_loader.full_variants_iterator():
            assert len(sv.alt_alleles) == 1

            aa = sv.alt_alleles[0]
            annotatable = aa.get_annotatable()
            result = pipeline.annotate(annotatable)
            liftover_annotatable: VCFAllele = \
                cast(VCFAllele, result.get("target_annotatable"))
            if liftover_annotatable is None:
                logger.error("can't liftover %s", aa)
                continue
            liftover_cshl_variant = VariantDetails.from_vcf(
                liftover_annotatable.chrom, liftover_annotatable.pos,
                liftover_annotatable.ref,
                liftover_annotatable.alt)

            summary_line = [
                liftover_cshl_variant.chrom,
                str(liftover_cshl_variant.cshl_position),
                liftover_cshl_variant.cshl_variant,
            ]
            frequency_data = [
                str(aa.attributes.get("af_parents_called_count", "")),
                str(aa.attributes.get("af_parents_called_percent", "")),
                str(aa.attributes.get("af_allele_count", "")),
                str(aa.attributes.get("af_allele_freq", "")),
            ]
            toomany_line = [
                liftover_cshl_variant.chrom,
                str(liftover_cshl_variant.cshl_position),
                liftover_cshl_variant.cshl_variant,
            ]

            families_data = []
            for fv in fvs:
                fa = cast(FamilyAllele, fv.alt_alleles[0])

                fdata = [
                    fa.family_id,
                    mat2str(fa.best_state),
                    fa.family_attributes["read_counts"],
                ]
                families_data.append(":".join(fdata))

            if len(families_data) < 20:
                summary_line.append(";".join(families_data))
                summary_line.extend(frequency_data)
                output_summary.write("\t".join(summary_line))
                output_summary.write("\n")
            else:
                summary_line.append("TOOMANY")
                summary_line.extend(frequency_data)
                output_summary.write("\t".join(summary_line))
                output_summary.write("\n")

                toomany_line.append(";".join(families_data))
                output_toomany.write("\t".join(toomany_line))
                output_toomany.write("\n")


class LiftoverTool(abc.ABC):
    """Liftover tools base class."""

    def __init__(
        self, description: str,
        default_output: str,
    ) -> None:
        self.description = description
        self.default_output = default_output
        self.cli_args: argparse.Namespace = argparse.Namespace()
        self.source_genome: ReferenceGenome | None = None

    def build_liftover_pipeline(
        self,
        grr: GenomicResourceRepo,
    ) -> AnnotationPipeline:
        """Build liftover annotator based on the selected mode."""
        if self.cli_args.mode not in {"bcf_liftover", "basic_liftover"}:
            raise ValueError(f"unknown liftover mode: {self.cli_args.mode}")
        annotator_type = "liftover_annotator"
        if self.cli_args.mode == "basic_liftover":
            annotator_type = "basic_liftover_annotator"

        pipeline_config = textwrap.dedent(
            f"""
            - {annotator_type}:
                chain: {self.cli_args.chain}
                source_genome: {self.cli_args.source_genome}
                target_genome: {self.cli_args.target_genome}
                attributes:
                - source: liftover_annotatable
                  name: target_annotatable
            """,
        )

        pipeline = load_pipeline_from_yaml(pipeline_config, grr)
        pipeline.open()

        return pipeline

    def build_cli_arguments_parser(
        self,
    ) -> argparse.ArgumentParser:
        """Create CLI parser."""
        parser = argparse.ArgumentParser(description=self.description)

        VerbosityConfiguration.set_arguments(parser)
        FamiliesLoader.cli_arguments(parser)

        context_providers_add_argparser_arguments(
            parser,
            skip_cli_annotation_context=True,
        )

        parser.add_argument(
            "-c", "--chain", help="chain resource id",
            default="liftover/hg19ToHg38")

        parser.add_argument(
            "-t", "--target-genome", help="target genome",
            default="hg38/genomes/GRCh38-hg38")

        parser.add_argument(
            "-s", "--source-genome", help="source genome",
            default="hg19/genomes/GATK_ResourceBundle_5777_b37_phiX174")

        parser.add_argument(
            "-o", "--output", help="output filename",
            default=self.default_output)

        parser.add_argument(
            "--region",
            type=str,
            dest="region",
            metavar="region",
            default=None,
            help="region to convert [default: None] "
            "ex. chr1:1-10000. ",
        )

        parser.add_argument(
            "--mode",
            type=str,
            dest="mode",
            metavar="mode",
            default="bcf_liftover",
            help="mode to use for liftover: 'bcf_liftover' or 'basic_liftover'",
        )

        return parser

    def run(self,
        argv: list[str] | None = None,
        grr: GenomicResourceRepo | None = None,
    ) -> None:
        """Liftover tool main function."""
        parser = self.build_cli_arguments_parser()

        if argv is None:
            argv = sys.argv[1:]
        assert argv is not None
        self.cli_args = parser.parse_args(argv)

        VerbosityConfiguration.set(self.cli_args)
        context_providers_init(
            **vars(self.cli_args), skip_cli_annotation_context=True)
        genomic_context = get_genomic_context()

        if grr is None:
            grr = genomic_context.get_genomic_resources_repository()
        if grr is None:
            raise ValueError("no valid GRR configured")

        self.source_genome = build_reference_genome_from_resource(
            grr.get_resource(self.cli_args.source_genome))
        assert self.source_genome is not None
        self.source_genome.open()

        pipeline = self.build_liftover_pipeline(
            grr,
        )
        region = None
        if self.cli_args.region is not None:
            region = Region.from_str(self.cli_args.region)

        self.liftover_variants(
            pipeline,
            region)

    @abc.abstractmethod
    def liftover_variants(
        self,
        pipeline: AnnotationPipeline,
        region: Region | None = None,
    ) -> None:
        """Liftover variants abstract method."""


class CNVLiftoverTool(LiftoverTool):
    """CNV liftover tool class."""

    def __init__(self) -> None:
        super().__init__("liftover CNV variants", "cnv_liftover.tsv")

    def build_cli_arguments_parser(
        self,
    ) -> argparse.ArgumentParser:
        """Create CLI parser."""
        parser = super().build_cli_arguments_parser()
        CNVLoader.cli_arguments(parser)
        return parser

    def liftover_variants(
        self,
        pipeline: AnnotationPipeline,
        region: Region | None = None,
    ) -> None:
        """Liftover CNV variants method."""
        assert self.source_genome is not None
        variants_loader = _build_variant_loader(
            CNVLoader, self.cli_args, self.source_genome)

        assert isinstance(variants_loader, CNVLoader)
        output_filename = _region_output_filename(
            self.cli_args.output, region,
        )
        _liftover_cnv_variants(
            output_filename,
            variants_loader,
            pipeline,
            region,
        )


def cnv_liftover_main(
    argv: list[str] | None = None,
    grr: GenomicResourceRepo | None = None,
) -> None:
    """CNV liftover tool main function."""
    tool = CNVLiftoverTool()
    tool.run(argv=argv, grr=grr)


class DaeLiftoverTool(LiftoverTool):
    """DAE liftover tool class."""

    def __init__(self) -> None:
        super().__init__(
            "liftover DAE transmitted variants",
            "transmitted_liftover")

    def build_cli_arguments_parser(
        self,
    ) -> argparse.ArgumentParser:
        """Create CLI parser."""
        parser = super().build_cli_arguments_parser()
        DaeTransmittedLoader.cli_arguments(parser)
        return parser

    def liftover_variants(
        self,
        pipeline: AnnotationPipeline,
        region: Region | None = None,
    ) -> None:
        """Liftover CNV variants method."""
        assert self.source_genome is not None
        variants_loader = _build_variant_loader(
            DaeTransmittedLoader, self.cli_args, self.source_genome)

        assert isinstance(variants_loader, DaeTransmittedLoader)
        output_filename = _region_output_filename(
            self.cli_args.output, region,
        )
        _liftover_dae_variants(
            output_filename,
            variants_loader,
            pipeline,
            region,
        )


def dae_liftover_main(
    argv: list[str] | None = None,
    grr: GenomicResourceRepo | None = None,
) -> None:
    """DAE liftover tool main function."""
    tool = DaeLiftoverTool()
    tool.run(argv=argv, grr=grr)


class DenovoLiftoverTool(LiftoverTool):
    """Denovo liftover tool class."""

    def __init__(self) -> None:
        super().__init__(
            "lliftover de Novo variants",
            "denovo_liftover.txt")

    def build_cli_arguments_parser(
        self,
    ) -> argparse.ArgumentParser:
        """Create CLI parser."""
        parser = super().build_cli_arguments_parser()
        DenovoLoader.cli_arguments(parser)
        return parser

    def liftover_variants(
        self,
        pipeline: AnnotationPipeline,
        region: Region | None = None,
    ) -> None:
        """Liftover CNV variants method."""
        assert self.source_genome is not None
        variants_loader = _build_variant_loader(
            DenovoLoader, self.cli_args, self.source_genome)

        assert isinstance(variants_loader, DenovoLoader)
        output_filename = _region_output_filename(
            self.cli_args.output, region,
        )
        _liftover_denovo_variants(
            output_filename,
            variants_loader,
            pipeline,
            region,
        )


def denovo_liftover_main(
    argv: list[str] | None = None,
    grr: GenomicResourceRepo | None = None,
) -> None:
    """Denovo liftover tool main function."""
    tool = DenovoLiftoverTool()
    tool.run(argv=argv, grr=grr)
