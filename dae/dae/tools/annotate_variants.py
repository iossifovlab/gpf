#!/usr/bin/env python

import argparse
import os.path
import sys
import time
from typing import Any

import pysam

from dae.effect_annotation.annotator import EffectAnnotator
from dae.effect_annotation.effect import AnnotationEffect
from dae.genomic_resources.gene_models import (
    GeneModels,
    build_gene_models_from_file,
)
from dae.genomic_resources.reference_genome import (
    ReferenceGenome,
    build_reference_genome_from_file,
)


def cli_genome_options(
        parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Create parser options for reference genome and gene models."""
    genome_group = parser.add_argument_group("genome specification")

    genome_group.add_argument(
        "--gene-models-id",
        "-T",
        help="gene models ID <RefSeq, CCDS, knownGene>",
    )
    genome_group.add_argument(
        "--gene-models-filename",
        "--Traw",
        help="outside gene models file path",
    )
    genome_group.add_argument(
        "--gene-models-fileformat",
        "--TrawFormat",
        help="outside gene models format (refseq, ccds, knowngene)",
        action="store",
    )
    genome_group.add_argument(
        "--gene-mapping-filename",
        "-I",
        help="geneIDs mapping file",
        default=None,
        action="store",
    )
    genome_group.add_argument(
        "--genome-id",
        "-G",
        help="genome ID <GATK_ResourceBundle_5777_b37_phiX174, hg19> ",
        action="store",
    )
    genome_group.add_argument(
        "--genome-filename",
        "--Graw",
        help="outside genome file name",
        action="store",
    )

    genome_group.add_argument(
        "--promoter-len",
        "-P",
        help="promoter length",
        default=0,
        type=int,
        dest="promoter_len",
    )

    return parser


def parse_cli_genome_options(
    args: argparse.Namespace,
) -> tuple[ReferenceGenome | None, GeneModels | None]:
    """Parse reference genome and gene models options."""
    genomic_sequence = None
    gene_models = None
    if args.gene_models_filename:
        gene_models = build_gene_models_from_file(
            args.gene_models_filename,
            file_format=args.gene_models_fileformat,
            gene_mapping_file_name=args.gene_mapping_filename,
        )
    if args.genome_filename:
        genomic_sequence = build_reference_genome_from_file(
            args.genome_filename)
        genomic_sequence = genomic_sequence.open()
    if gene_models and genomic_sequence:
        return genomic_sequence, gene_models

    if genomic_sequence is None or gene_models is None:
        return None, None
    return None, None


def cli_variants_options(parser: argparse.ArgumentParser) -> None:
    """Configure parser for variant specifying options."""
    location_group = parser.add_argument_group("variants location")
    location_group.add_argument(
        "--chrom", "-c", help="chromosome column number/name", action="store",
    )
    location_group.add_argument(
        "--pos", "-p", help="position column number/name", action="store",
    )
    location_group.add_argument(
        "--location",
        "-x",
        help="location (chr:pos) column number/name",
        action="store",
    )

    variants_group = parser.add_argument_group("variants specification")
    variants_group.add_argument(
        "--variant", "-v", help="variant column number/name", action="store",
    )
    variants_group.add_argument(
        "--ref",
        "-r",
        help="reference allele column number/name",
        action="store",
    )
    variants_group.add_argument(
        "--alt",
        "-a",
        help="alternative allele column number/name",
        action="store",
    )

    parser.add_argument(
        "--no-header",
        "-H",
        help="no header in the input file",
        default=False,
        action="store_true",
    )

    # variants_group.add_argument(
    #     "-t", help="type of mutation column number/name", action="store"
    # )
    # variants_group.add_argument(
    #     "-q", help="seq column number/name", action="store"
    # )
    # variants_group.add_argument(
    #     "-l", help="length column number/name", action="store"
    # )


def parse_cli_variants_options(args: argparse.Namespace) -> dict[str, Any]:
    """Parse variant definition options."""
    columns = {}
    if args.location is None:
        if args.chrom is None and args.pos is None:
            # default is location
            columns["loc"] = "location"
        else:
            assert args.chrom is not None and args.pos is not None
            columns["chrom"] = args.chrom
            columns["position"] = args.pos
    else:
        assert args.chrom is None and args.pos is None
        columns["loc"] = args.location

    if args.variant is None:
        if args.ref is None and args.alt is None:
            # default is variant
            columns["var"] = "variant"
        else:
            assert args.ref is not None and args.alt is not None
            columns["ref"] = args.ref
            columns["alt"] = args.alt
    else:
        assert args.ref is None and args.alt is None
        columns["var"] = args.variant
    return columns


def cli(argv: list[str] | None = None) -> None:
    """Annotate variants main function."""
    # pylint: disable=too-many-branches,too-many-statements
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="variants effect annotator",
        conflict_handler="resolve",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    cli_genome_options(parser)
    cli_variants_options(parser)

    parser.add_argument(
        "input_filename", nargs="?", help="input variants file name",
    )
    parser.add_argument(
        "output_filename", nargs="?", help="output file name (default: stdout)",
    )

    args = parser.parse_args(argv)
    genomic_sequence, gene_models = parse_cli_genome_options(args)
    assert genomic_sequence is not None
    assert gene_models is not None
    annotator = EffectAnnotator(
        genomic_sequence, gene_models, promoter_len=args.promoter_len,
    )

    variant_columns = parse_cli_variants_options(args)

    if args.input_filename == "-" or args.input_filename is None:
        infile = sys.stdin
    else:
        assert os.path.exists(args.input_filename), args.input_filename
        # pylint: disable=consider-using-with
        infile = open(args.input_filename, "r")

    if args.output_filename is None:
        outfile = sys.stdout
    else:
        # pylint: disable=consider-using-with
        outfile = open(args.output_filename, "w")

    start = time.time()
    header = None
    assert not args.no_header, args

    if args.no_header:
        assert False
        for key, value in variant_columns.items():
            variant_columns[key] = int(value)
    else:

        line = infile.readline().strip()
        header = [c.strip() for c in line.split("\t")]
        for key, value in variant_columns.items():
            assert value in header
            variant_columns[key] = header.index(value)
        header.extend(["effectType", "effectGene", "effectDetails"])

        print("header:", header, variant_columns, file=sys.stderr)
        print("\t".join(header), file=sys.stderr)
        print("\t".join(header), file=outfile)

    counter = 0
    for counter, line in enumerate(infile):
        if line[0] == "#":
            continue
        columns = [c.strip() for c in line.split("\t")]
        variant = {
            key: columns[value] for key, value in variant_columns.items()
        }
        effects = annotator.do_annotate_variant(**variant)
        desc = AnnotationEffect.effects_description(effects)
        columns.extend(desc)
        print("\t".join(columns), file=sys.stderr)
        print("\t".join(columns), file=outfile)

        if (counter + 1) % 1000 == 0:
            elapsed = time.time() - start
            print(
                f"processed {counter + 1} lines in {elapsed:0.2f} sec",
                file=sys.stderr,
            )

    infile.close()
    if args.output_filename:
        outfile.close()

    elapsed = time.time() - start
    print(80 * "=", file=sys.stderr)
    print(
        f"DONE: {counter + 1} variants in {elapsed:0.2f} sec", file=sys.stderr,
    )
    print(80 * "=", file=sys.stderr)


def cli_vcf(argv: list[str] | None = None) -> None:
    """Annotate variants main function for annotating VCF file."""
    # pylint: disable=too-many-branches,too-many-statements,too-many-locals
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="VCF variants effect annotator",
        conflict_handler="resolve",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    cli_genome_options(parser)
    parser.add_argument("input_filename", help="input VCF variants file name")
    parser.add_argument(
        "output_filename", nargs="?", help="output file name (default: stdout)",
    )

    args = parser.parse_args(argv)
    genomic_sequence, gene_models = parse_cli_genome_options(args)
    assert genomic_sequence is not None
    assert gene_models is not None
    annotator = EffectAnnotator(
        genomic_sequence, gene_models, promoter_len=args.promoter_len,
    )

    assert os.path.exists(args.input_filename), args.input_filename
    # pylint: disable=no-member
    infile = pysam.VariantFile(args.input_filename)

    if args.output_filename is None:
        outfile = sys.stdout
    else:
        # pylint: disable=consider-using-with
        outfile = open(args.output_filename, "w")

    start = time.time()
    # Transfer VCF header
    header = infile.header
    header.add_meta(
        "variant_effect_annotation", "GPF variant effects annotation",
    )
    header.add_meta(
        "variant_effect_annotation_command", f"'{' '.join(sys.argv)}'",
    )

    header.info.add("ET", ".", "String", "effected type")
    header.info.add("EG", ".", "String", "effected gene")
    header.info.add("ED", ".", "String", "effect details")

    print(str(header), file=outfile, end="")
    counter = 0
    for counter, variant in enumerate(infile):
        effect_types = []
        effect_genes = []
        effect_details = []
        egs = ""
        eds = ""
        if variant.alts is not None:
            for alt in variant.alts:
                effects = annotator.do_annotate_variant(
                    chrom=variant.chrom,
                    pos=variant.pos,
                    ref=variant.ref,
                    alt=alt,
                )
                ets, egs, eds = AnnotationEffect.effects_description(effects)
                eds = eds.replace(";", "|")
                effect_types.append(ets)
                effect_genes.append(egs)
                effect_details.append(eds)

        variant.info["ET"] = ",".join(effect_types)
        variant.info["EG"] = egs
        variant.info["ED"] = eds

        print(str(variant), file=outfile, end="")
        if (counter + 1) % 1000 == 0:
            elapsed = time.time() - start
            print(
                f"processed {counter + 1} variants in {elapsed:0.2f} sec",
                file=sys.stderr,
            )

    infile.close()
    if args.output_filename:
        outfile.close()

    elapsed = time.time() - start
    print(80 * "=", file=sys.stderr)
    print(
        f"DONE: {counter + 1} variants in {elapsed:0.2f} sec", file=sys.stderr,
    )
    print(80 * "=", file=sys.stderr)


if __name__ == "__main__":
    cli(sys.argv[1:])
