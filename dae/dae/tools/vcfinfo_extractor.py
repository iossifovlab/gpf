#!/usr/bin/env python

import argparse
import sys
import logging
import os

import pysam

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.variants.variant import SummaryVariantFactory


def main(argv, gpf_instance=None):
    parser = argparse.ArgumentParser()

    parser.add_argument('--verbose', '-V', action='count', default=0)

    parser.add_argument(
        "vcf_filename",
        type=str,
        metavar="<VCF file>",
        help="VCF filename. "
    )

    parser.add_argument(
        "--columns", "-c",
        type=str,
        default=None,
        metavar="<C1,C2,C3...>",
        help="column separated list of INFO field values to be extracted"
    )

    parser.add_argument(
        "--region", "-r", action="store", type=str, default=None)
    parser.add_argument(
        "--output", "-o",
        type=str,
        metavar="<output filename>",
        help="output filename")

    argv = parser.parse_args(argv)
    assert argv.output is not None

    if argv.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif argv.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif argv.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    if gpf_instance is None:
        gpf_instance = GPFInstance()

    assert os.path.exists(argv.vcf_filename)
    vcf = pysam.VariantFile(argv.vcf_filename)

    assert argv.columns is not None
    info_columns = [c.strip() for c in argv.columns.split(",")]
    header = [
        "CHROM",
        "POS",
        "chrom",
        "position",
        "location",
        "variant",
        "REF",
        "ALT",
        "ID"
    ]
    header.extend(info_columns)

    with open(argv.output, "wt") as output:
        output.write("\t".join(header))
        output.write("\n")

        for summary_index, vcf_variant in enumerate(vcf(argv.region)):
            sv = SummaryVariantFactory.summary_variant_from_vcf(
                vcf_variant, summary_index)
            sa = sv.alt_alleles[0]

            assert len(vcf_variant.alts) == 1
            line = [
                vcf_variant.chrom,
                vcf_variant.pos,
                sa.chromosome,
                sa.cshl_position,
                sa.cshl_location,
                sa.cshl_variant,
                vcf_variant.ref,
                vcf_variant.alts[0],
                vcf_variant.id,
            ]
            for info_id in info_columns:
                value = None
                if info_id.endswith("_percent"):
                    iid = info_id[:-8]
                    ivalue = vcf_variant.info.get(iid)
                    if ivalue:
                        value = float(ivalue[0])
                        value = value*100.0
                else:
                    ivalue = vcf_variant.info.get(info_id)
                    if ivalue:
                        value = float(ivalue[0])
                line.append(value)

            outline = []
            for v in line:
                if v is None:
                    outline.append("")
                else:
                    outline.append(str(v))

            output.write("\t".join(outline))
            output.write("\n")

            if summary_index % 10000 == 0:
                print(f"progress {argv.region}: {summary_index}")


if __name__ == "__main__":
    main(sys.argv[1:])
