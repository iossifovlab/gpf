#!/usr/bin/env python

import sys
import argparse
import logging
import textwrap
from typing import cast

from collections import defaultdict, Counter

from dae.utils.variant_utils import mat2str
from dae.variants.variant import VariantDetails

from dae.genomic_resources.reference_genome import \
    open_reference_genome_from_resource
from dae.annotation.annotation_factory import \
    build_annotation_pipeline

from dae.annotation.annotatable import VCFAllele

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.backends.dae.loader import DaeTransmittedLoader
from dae.pedigrees.loader import FamiliesLoader
from dae.tools.stats_liftover import save_liftover_stats


logger = logging.getLogger("dae_liftover")


def parse_cli_arguments():
    parser = argparse.ArgumentParser(
        description="liftover denovo variants to hg38")

    parser.add_argument('--verbose', '-V', action='count', default=0)

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
        default="stats.txt"
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
        "ex. chr1:1-10000. "
    )

    return parser


def main(argv=sys.argv[1:], gpf_instance=None):
    if gpf_instance is None:
        gpf_instance = GPFInstance()

    parser = parse_cli_arguments()
    argv = parser.parse_args(argv)

    if argv.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif argv.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif argv.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    logging.getLogger("dae.effect_annotation").setLevel(logging.WARNING)

    grr = gpf_instance.grr
    source_genome_resource = grr.get_resource(argv.source_genome)
    assert source_genome_resource is not None
    source_genome = open_reference_genome_from_resource(source_genome_resource)
    assert source_genome is not None

    families_filename, families_params = \
        FamiliesLoader.parse_cli_arguments(argv)

    families_loader = FamiliesLoader(
        families_filename, **families_params
    )
    families = families_loader.load()

    variants_filenames, variants_params = \
        DaeTransmittedLoader.parse_cli_arguments(argv)

    variants_loader = DaeTransmittedLoader(
        families,
        variants_filenames,
        params=variants_params,
        genome=source_genome,
    )

    summary_filename = f"{argv.output_prefix}.txt"
    toomany_filename = f"{argv.output_prefix}-TOOMANY.txt"
    if argv.region is not None:
        region = argv.region
        logger.info(f"resetting regions (region): {region}")
        variants_loader.reset_regions(region)
        summary_filename = f"{argv.output_prefix}-{region}.txt"
        toomany_filename = f"{argv.output_prefix}-TOOMANY-{region}.txt"

    pipeline_config = textwrap.dedent(
        f"""
        - effect_annotator:
            gene_models: {argv.source_gene_models}
            genome: {argv.source_genome}
            attributes:
            - source: "worst_effect"
              destination: "source_worst_effect"
            - source: "gene_effects"
              destination: "source_gene_effects"
            - source: "effect_details"
              destination: "source_effect_details"

        - liftover_annotator:
            chain: {argv.chain}
            target_genome: {argv.target_genome}
            attributes:
            - source: liftover_annotatable
              destination: target_annotatable

        - effect_annotator:
            gene_models: {argv.target_gene_models}
            genome: {argv.target_genome}
            input_annotatable: target_annotatable
            attributes:
            - source: "worst_effect"
              destination: "target_worst_effect"
            - source: "gene_effects"
              destination: "target_gene_effects"
            - source: "effect_details"
              destination: "target_effect_details"

        """
    )

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=gpf_instance.grr)

    target_stats = defaultdict(Counter)

    with open(summary_filename, "wt") as output_summary, \
            open(toomany_filename, "wt") as output_toomany:

        summary_header = [
            "#chr", "position", "variant",
            "familyData",
            "all.nParCalled", "all.prcntParCalled",
            "all.nAltAlls", "all.altFreq"
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

            source_worst_effect = result.get("source_worst_effect")
            target_worst_effect = result.get("target_worst_effect")
            target_stats[source_worst_effect]["source"] += 1

            if liftover_annotatable is None:
                logger.error(f"can't liftover {aa}")
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
                fa = fv.alt_alleles[0]

                fdata = [
                    fa.family_id,
                    mat2str(fa.best_state),
                    mat2str(
                        fa.family_attributes.get("read_counts"), col_sep=" ")
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

    save_liftover_stats(target_stats, argv.stats)

if __name__ == "__main__":
    main(sys.argv[1:])
