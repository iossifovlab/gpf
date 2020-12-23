#!/usr/bin/env python

import argparse
import sys
import logging
import os

import cyvcf2

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
    vcf = cyvcf2.VCF(argv.vcf_filename)

    assert argv.columns is not None
    info_columns = [c.strip() for c in argv.columns.split(",")]
    header = ["CHROM", "POS", "variant", "location", "REF", "ALT", "ID"]
    header.extend(info_columns)

    with open(argv.output, "wt") as output:
        output.write("\t".join(header))
        output.write("\n")

        for summary_index, vcf_variant in enumerate(vcf(argv.region)):
            sv = SummaryVariantFactory.summary_variant_from_vcf(
                vcf_variant, summary_index)
            sa = sv.alt_alleles[0]

            assert len(vcf_variant.ALT) == 1
            line = [
                vcf_variant.CHROM,
                vcf_variant.POS,
                sa.cshl_location,
                sa.cshl_variant,
                vcf_variant.REF,
                vcf_variant.ALT[0],
                vcf_variant.ID,
            ]
            for info_id in info_columns:
                if info_id.endswith("_percent"):
                    iid = info_id[:-8]
                    value = vcf_variant.INFO.get(iid)
                    if value is not None:
                        value = value*100.0
                else:
                    value = vcf_variant.INFO.get(info_id)
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
