import argparse
import logging
import pathlib
import sys
import textwrap
from collections import Counter, defaultdict
from contextlib import closing
from typing import Any, Optional

import pysam

from dae.annotation.annotatable import VCFAllele
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.context import CLIAnnotationContext
from dae.genomic_resources.genomic_context import get_genomic_context
from dae.genomic_resources.reference_genome import (
    ReferenceGenome,
    build_reference_genome_from_resource,
)
from dae.tools.stats_liftover import save_liftover_stats
from dae.utils.regions import Region
from dae.utils.verbosity_configuration import VerbosityConfiguration

logger = logging.getLogger("vcf_liftover")


def parse_cli_arguments() -> argparse.ArgumentParser:
    """Create CLI parser."""
    parser = argparse.ArgumentParser(
        description="liftover VCF variants")

    CLIAnnotationContext.add_context_arguments(parser)
    VerbosityConfiguration.set_arguments(parser)

    parser.add_argument(
        "--vcf", help="vcf file to liftover",
    )

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
        argv: Optional[list[str]] = None,
) -> None:
    """Liftover dae variants tool main function."""
    # pylint: disable=too-many-locals,too-many-statements
    if argv is None:
        argv = sys.argv[1:]

    parser = parse_cli_arguments()
    args = parser.parse_args(argv)

    VerbosityConfiguration.set(args)

    context = get_genomic_context()

    grr = context.get_genomic_resources_repository()
    if grr is None:
        raise ValueError("genomic resources repository not found")

    res = grr.get_resource(args.source_genome)
    if res is None:
        raise ValueError(f"source genome {args.source_genome} not found")

    source_genome = build_reference_genome_from_resource(res)
    if source_genome is None:
        raise ValueError(f"source genome {args.source_genome} not found")

    res = grr.get_resource(args.target_genome)
    if res is None:
        raise ValueError(f"target genome {args.target_genome} not found")
    target_genome = build_reference_genome_from_resource(res)
    if target_genome is None:
        raise ValueError(f"target genome {args.target_genome} not found")

    output_filename = f"{args.output_prefix}.vcf"
    region = None
    if args.region is not None:
        region = str(Region.from_str(args.region))
        output_filename = f"{args.output_prefix}-{region}.vcf"

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

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=grr)
    pipeline.open()

    target_stats: dict[str, Any] = defaultdict(Counter)

    with closing(pysam.VariantFile(args.vcf)) as infile:
        output_header = liftover_header(
            pathlib.Path(args.vcf),
            source_genome,
            target_genome)

    with closing(pysam.VariantFile(args.vcf)) as infile, \
            closing(pysam.VariantFile(
                output_filename, "w", header=output_header)) as outfile:
        for vcf_variant in infile.fetch(region=region):
            if vcf_variant.alts is None:
                logger.warning("skipping variant without alts: %s", vcf_variant)
                continue
            if vcf_variant.ref is None:
                logger.warning("skipping variant without ref: %s", vcf_variant)
                continue
            alleles = []
            for alt in vcf_variant.alts:
                annotatable = VCFAllele(
                    vcf_variant.chrom, vcf_variant.pos,
                    vcf_variant.ref, alt)
                result = pipeline.annotate(annotatable)
                target_annotatable = result["target_annotatable"]
                if target_annotatable is None:
                    continue
                alleles.append(target_annotatable)

            if len(alleles) < len(vcf_variant.alts):
                logger.warning(
                    "skipping variant without liftover: %s liftover to %s",
                    report_vcf_variant(vcf_variant), report_alleles(alleles))
                continue
            if not all(a.chrom == alleles[0].chrom for a in alleles):
                logger.warning(
                    "liftover alleles on different contigs: %s liftover to %s",
                    report_vcf_variant(vcf_variant), report_alleles(alleles))
                continue
            if not all(a.pos == alleles[0].pos for a in alleles):
                logger.warning(
                    "liftover alleles on different positions: %s "
                    "liftover to %s",
                    report_vcf_variant(vcf_variant), report_alleles(alleles))
                continue
            if not all(a.ref == alleles[0].ref for a in alleles):
                logger.warning(
                    "liftover alleles with different ref: %s liftover to %s",
                    report_vcf_variant(vcf_variant), report_alleles(alleles))
                continue
            vcf_variant.translate(output_header)
            vcf_variant.contig = alleles[0].chrom
            vcf_variant.pos = alleles[0].pos
            vcf_variant.ref = alleles[0].ref
            vcf_variant.alts = tuple(a.alt for a in alleles)

            outfile.write(vcf_variant)

    save_liftover_stats(target_stats, args.stats)


def report_vcf_variant(vcf_variant: pysam.VariantRecord) -> str:
    """Report VCF variant."""
    return (
        f"({vcf_variant.chrom}:{vcf_variant.pos} "
        f"{vcf_variant.ref} > "
        f"{','.join(vcf_variant.alts) if vcf_variant.alts else '.'})"
    )


def report_alleles(alleles: list[VCFAllele]) -> str:
    """Report alleles."""
    if not alleles:
        return "(none)"
    return ";".join([
        f"({a.chrom}:{a.pos} {a.ref} > {a.alt})" for a in alleles
    ])


def liftover_header(
    infile: pathlib.Path,
    source_genome: ReferenceGenome,
    target_genome: ReferenceGenome,
) -> pysam.VariantHeader:
    """Create liftover VCF header."""
    with closing(pysam.TabixFile(str(infile))) as tabix_file:
        contigs = tabix_file.contigs
    target_contigs = []
    for chrom in contigs:
        name = f"chr{chrom}"
        target_contigs.append(name)

    with closing(pysam.VariantFile(str(infile))) as vcf, \
        closing(pysam.VariantFile(
                "tmp.vcf", "w", header=vcf.header)) as tmp:
        pass

    with open("tmp.vcf", "rt") as tmp:
        lines = tmp.readlines()
        outheader = []
        contig_index = None
        for index, line in enumerate(lines):
            if line.startswith("##contig"):
                if contig_index is None:
                    contig_index = index
                continue
            outheader.append(line)
    outcontigs = [f"##contig=<ID={contig}>\n" for contig in target_contigs]
    if contig_index is None:
        raise ValueError("No contig lines found in header")

    with open("tmp.vcf", "wt") as tmp:
        for index, line in enumerate(outheader):
            if index == contig_index:
                for contig in outcontigs:
                    tmp.write(contig)
            tmp.write(line)
        tmp.write(
            f"##source_reference={source_genome.resource_id}\n")
        tmp.write(
            f"##target_reference={target_genome.resource_id}\n")
        tmp.write(
            f"##command=vcf_liftover {' '.join(sys.argv[1:])}\n")

    with closing(pysam.VariantFile("tmp.vcf")) as tmp:
        return tmp.header
