import argparse
import logging
import sys
import textwrap
from collections import Counter, defaultdict
from typing import Any, cast

from dae.annotation.annotatable import VCFAllele
from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.genomic_resources.reference_genome import (
    build_reference_genome_from_resource,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.pedigrees.loader import FamiliesLoader
from dae.tools.stats_liftover import save_liftover_stats
from dae.utils.variant_utils import mat2str
from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.variants.family_variant import FamilyAllele
from dae.variants.variant import VariantDetails
from dae.variants_loaders.dae.loader import DaeTransmittedLoader

logger = logging.getLogger("dae_liftover")


def parse_cli_arguments() -> argparse.ArgumentParser:
    """Create CLI parser."""
    parser = argparse.ArgumentParser(
        description="liftover denovo variants to hg38")
    VerbosityConfiguration.set_arguments(parser)
    FamiliesLoader.cli_arguments(parser)
    DaeTransmittedLoader.cli_arguments(parser)

    parser.add_argument(
        "-c", "--chain", help="chain resource id",
        default="liftover/hg19ToHg38")

    parser.add_argument(
        "-t", "--target-genome", help="target genome",
        default="hg38/genomes/GRCh38-hg38")
    parser.add_argument(
        "--target-gene-models", "--tgm", help="target gene models",
        default="hg38/gene_models/refGene_v20170601")

    parser.add_argument(
        "-s", "--source-genome", help="source genome",
        default="hg19/genomes/GATK_ResourceBundle_5777_b37_phiX174")
    parser.add_argument(
        "--source-gene-models", "--sgm", help="source gene models",
        default="hg19/gene_models/refGene_v20190211")

    parser.add_argument(
        "--stats", help="filename to store liftover statistics",
        default="stats.txt",
    )

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

    return parser


def main(
        argv: list[str] | None = None,
        gpf_instance: GPFInstance | None = None) -> None:
    """Liftover dae variants tool main function."""
    # pylint: disable=too-many-locals,too-many-statements
    if argv is None:
        argv = sys.argv[1:]
    if gpf_instance is None:
        gpf_instance = GPFInstance.build()

    parser = parse_cli_arguments()
    assert argv is not None
    args = parser.parse_args(argv)

    VerbosityConfiguration.set(args)

    grr = gpf_instance.grr
    source_genome = build_reference_genome_from_resource(
        grr.get_resource(args.source_genome))
    assert source_genome is not None
    source_genome.open()

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
        region = args.region
        logger.info("resetting regions (region): %s", region)
        variants_loader.reset_regions(region)
        summary_filename = f"{args.output_prefix}-{region}.txt"
        toomany_filename = f"{args.output_prefix}-TOOMANY-{region}.txt"

    pipeline_config = textwrap.dedent(
        f"""
        - effect_annotator:
            gene_models: {args.source_gene_models}
            genome: {args.source_genome}
            attributes:
            - source: "worst_effect"
              name: "source_worst_effect"
            - source: "gene_effects"
              name: "source_gene_effects"
            - source: "effect_details"
              name: "source_effect_details"

        - liftover_annotator:
            chain: {args.chain}
            source_genome: {args.source_genome}
            target_genome: {args.target_genome}
            attributes:
            - source: liftover_annotatable
              name: target_annotatable

        - effect_annotator:
            gene_models: {args.target_gene_models}
            genome: {args.target_genome}
            input_annotatable: target_annotatable
            attributes:
            - source: "worst_effect"
              name: "target_worst_effect"
            - source: "gene_effects"
              name: "target_gene_effects"
            - source: "effect_details"
              name: "target_effect_details"

        """,
    )

    pipeline = load_pipeline_from_yaml(pipeline_config, gpf_instance.grr)
    pipeline.open()

    target_stats: dict[str, Any] = defaultdict(Counter)

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
            annotatable: VCFAllele = cast(VCFAllele, aa.get_annotatable())
            result = pipeline.annotate(annotatable)
            liftover_annotatable: VCFAllele = \
                cast(VCFAllele, result.get("target_annotatable"))

            source_worst_effect = cast(str, result.get("source_worst_effect"))
            target_worst_effect = cast(str, result.get("target_worst_effect"))
            target_stats[source_worst_effect]["source"] += 1

            if liftover_annotatable is None:
                logger.error("can't liftover %s", aa)
                target_stats[source_worst_effect]["no_liftover"] += 1
                continue

            liftover_cshl_variant = VariantDetails.from_vcf(
                liftover_annotatable.chrom,
                liftover_annotatable.pos,
                liftover_annotatable.ref, liftover_annotatable.alt)

            target_stats[source_worst_effect][target_worst_effect] += 1

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
                    mat2str(
                        fa.family_attributes["read_counts"], col_sep=" "),
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

    save_liftover_stats(target_stats, args.stats)
