#!/usr/bin/env python

import argparse
import sys
import logging
import os

import pysam

from contextlib import closing
from functools import partial

from dae.utils.regions import Region
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.variants.attributes import TransmissionType
from dae.variants.variant import SummaryVariantFactory


def info_get(info, column=None):
    v = info.get(column)
    if v is None:
        return ""
    return v


def info_get_allele(info, column=None):
    v = info.get(column)
    if v is None:
        return ""
    return v[0]


def info_get_allele_percent(info, column=None):
    v = info.get(column)
    if v is None:
        return ""
    return float(v[0]) * 100.0


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
        gpf_instance = GPFInstance.build()

    assert argv.columns is not None
    info_columns = [c.strip() for c in argv.columns.split(",")]
    header = [
        "#CHROM",
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

    region = None
    if argv.region:
        if ":" in argv.region:
            region = Region.from_str(argv.region)
        elif "-" in argv.region:
            parts = argv.region.split("-")
            if len(parts) == 3:
                region = Region.from_str(f"{parts[0]}:{parts[1]}-{parts[2]}")
            elif len(parts) == 2:
                region = Region.from_str(f"{parts[0]}:{parts[1]}")
            else:
                raise ValueError(f"unexpected region format {argv.region}")
    print(f"processing region: {region}")

    assert os.path.exists(argv.vcf_filename)
    with closing(pysam.VariantFile(argv.vcf_filename)) as vcf, \
            open(argv.output, "wt") as output:

        header_info = vcf.header.info
        accessors = {}
        for column in info_columns:
            if column not in header_info and column.endswith("_percent"):
                base_column = column[:-8]
                assert base_column in header_info
                accessors[column] = partial(
                    info_get_allele_percent, column=base_column)

            elif header_info[column].number == 1:
                accessors[column] = partial(info_get, column=column)

            elif header_info[column].number == "A":
                accessors[column] = partial(info_get_allele, column=column)

            else:
                raise ValueError("unexpected info number type")

        if region is None:
            vcf_iterator = vcf.fetch()
        else:
            vcf_iterator = vcf.fetch(region.chrom, region.begin, region.end)

        output.write("\t".join(header))
        output.write("\n")

        for summary_index, vcf_variant in enumerate(vcf_iterator):
            assert len(vcf_variant.alts) == 1, vcf_variant

            if not region.isin(vcf_variant.chrom, vcf_variant.pos):
                continue

            sv = SummaryVariantFactory.summary_variant_from_vcf(
                vcf_variant, summary_index,
                transmission_type=TransmissionType.transmitted)

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
                accessor = accessors[info_id]
                value = accessor(vcf_variant.info)
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
