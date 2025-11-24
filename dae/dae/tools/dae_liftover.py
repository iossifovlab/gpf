import argparse
import logging
import sys
from typing import cast

from dae.annotation.liftover_annotator import (
    basic_liftover_variant,
    bcf_liftover_variant,
)
from dae.genomic_resources.genomic_context import (
    context_providers_add_argparser_arguments,
    context_providers_init,
    get_genomic_context,
)
from dae.genomic_resources.liftover_chain import (
    build_liftover_chain_from_resource,
)
from dae.genomic_resources.reference_genome import (
    build_reference_genome_from_resource,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.pedigrees.loader import FamiliesLoader
from dae.utils.regions import Region
from dae.utils.variant_utils import mat2str
from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.variants.family_variant import FamilyAllele
from dae.variants.variant import VariantDetails
from dae.variants_loaders.dae.loader import DaeTransmittedLoader

logger = logging.getLogger("dae_liftover")


def build_cli_arguments_parser() -> argparse.ArgumentParser:
    """Create CLI parser."""
    parser = argparse.ArgumentParser(
        description="liftover variants in DAE transmitted format")
    VerbosityConfiguration.set_arguments(parser)
    FamiliesLoader.cli_arguments(parser)
    DaeTransmittedLoader.cli_arguments(parser)

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
        "-o", "--output-prefix", help="output filename prefix",
        default="transmitted")

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


def main(
    argv: list[str] | None = None,
    grr: GenomicResourceRepo | None = None,
) -> None:
    """Liftover dae variants tool main function."""
    # pylint: disable=too-many-locals,too-many-statements
    if argv is None:
        argv = sys.argv[1:]

    parser = build_cli_arguments_parser()
    assert argv is not None
    args = parser.parse_args(argv)

    VerbosityConfiguration.set(args)
    context_providers_init(
        **vars(args), skip_cli_annotation_context=True)
    genomic_context = get_genomic_context()

    if grr is None:
        grr = genomic_context.get_genomic_resources_repository()
    if grr is None:
        raise ValueError("no valid GRR configured")

    source_genome = build_reference_genome_from_resource(
        grr.get_resource(args.source_genome))
    assert source_genome is not None
    source_genome.open()
    target_genome = build_reference_genome_from_resource(
        grr.get_resource(args.target_genome))
    assert target_genome is not None
    target_genome.open()

    chain = build_liftover_chain_from_resource(
        grr.get_resource(args.chain))
    assert chain is not None
    chain.open()

    families_filenames, families_params = \
        FamiliesLoader.parse_cli_arguments(args)
    families_filename = families_filenames[0]

    families_loader = FamiliesLoader(
        families_filename, **families_params,
    )
    families = families_loader.load()

    variants_filenames, variants_params = \
        DaeTransmittedLoader.parse_cli_arguments(args)

    variants_loader = DaeTransmittedLoader(
        families,
        variants_filenames,  # type: ignore
        params=variants_params,
        genome=source_genome,
    )

    summary_filename = f"{args.output_prefix}.txt"
    toomany_filename = f"{args.output_prefix}-TOOMANY.txt"
    if args.region is not None:
        region = Region.from_str(args.region)
        logger.info("resetting regions (region): %s", region)
        variants_loader.reset_regions([region])
        summary_filename = f"{args.output_prefix}-{region}.txt"
        toomany_filename = f"{args.output_prefix}-TOOMANY-{region}.txt"
    logger.info("summary output: %s", summary_filename)
    logger.info("toomany output: %s", toomany_filename)

    if args.mode == "bcf_liftover":
        liftover_variant_func = bcf_liftover_variant
    elif args.mode == "basic_liftover":
        liftover_variant_func = basic_liftover_variant
    else:
        raise ValueError(f"Invalid mode: {args.mode}")

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
            assert aa.reference is not None
            assert aa.alternative is not None

            lo_variant = liftover_variant_func(
                aa.chrom, aa.position, aa.reference, [aa.alternative],
                chain,
                source_genome=source_genome,
                target_genome=target_genome,
            )
            if lo_variant is None:
                logger.warning(
                    "skipping variant without liftover: %s", sv)
                continue
            chrom, pos, ref, alts = lo_variant
            assert len(alts) == 1

            liftover_cshl_variant = VariantDetails.from_vcf(
                chrom, pos, ref, alts[0])

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
