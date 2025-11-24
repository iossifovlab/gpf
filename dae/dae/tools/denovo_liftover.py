import argparse
import logging
import sys
from typing import cast

from dae.annotation.annotatable import VCFAllele
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
from dae.utils.variant_utils import mat2str
from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.variants.family_variant import FamilyAllele
from dae.variants_loaders.dae.loader import DenovoLoader

logger = logging.getLogger("denovo_liftover")


def build_cli_arguments_parser() -> argparse.ArgumentParser:
    """Create CLI parser."""
    parser = argparse.ArgumentParser(description="liftover denovo variants")

    VerbosityConfiguration.set_arguments(parser)
    FamiliesLoader.cli_arguments(parser)
    DenovoLoader.cli_arguments(parser)

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
        default="denovo_liftover.txt")

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
    """Liftover de Novo variants tool main function."""
    # pylint: disable=too-many-locals
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
        DenovoLoader.parse_cli_arguments(args)

    variants_loader = DenovoLoader(
        families,
        variants_filenames,  # type: ignore
        params=variants_params,
        genome=source_genome,
    )

    if args.mode == "bcf_liftover":
        liftover_variant_func = bcf_liftover_variant
    elif args.mode == "basic_liftover":
        liftover_variant_func = basic_liftover_variant
    else:
        raise ValueError(f"Invalid mode: {args.mode}")

    with open(args.output, "wt") as output:

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

            for fv in fvs:
                fa = cast(FamilyAllele, fv.alt_alleles[0])

                line = [
                    chrom, str(pos),
                    ref, alts[0],

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
