#!/usr/bin/env python
# pylint: disable=invalid-name
import argparse
import csv
import pandas as pd


def get_argument_parser():
    """Create argument parser for denovo2vcf."""
    parser = argparse.ArgumentParser(description="Convert DAE file to vcf")

    parser.add_argument(
        "pedigree",
        type=str,
        metavar="<pedigree filename>",
        help="families file in pedigree format",
    )
    parser.add_argument(
        "denovo",
        type=str,
        metavar="<denovo filename>",
        help="denovo file to import",
    )
    parser.add_argument(
        "-o",
        "--out",
        type=str,
        default="./output.vcf",
        dest="out",
        metavar="output filepath",
        help="output filepath. If none specified, output file is output.vcf",
    )
    parser.add_argument(
        "--pedigree-delimiter",
        help="delimiter used in the split column in "
        'pedigree; defaults to "\\t"',
        default="\t",
        action="store",
    )
    parser.add_argument(
        "--denovo-delimiter",
        help="delimiter used in the split column in "
        'denovo; defaults to "\\t"',
        default="\t",
        action="store",
    )
    parser.add_argument(
        "--pedigree-personId",
        help="personId column name used in pedigree; "
        'defaults to "personId"',
        default="personId",
        action="store",
    )
    parser.add_argument(
        "--denovo-personId",
        help="personId column name used in denovo; " 'defaults to "personId"',
        default="personId",
        action="store",
    )
    parser.add_argument(
        "--denovo-chromosome",
        help="chromosome column name used in denovo; " 'defaults to "chrom"',
        default="chrom",
        action="store",
    )
    parser.add_argument(
        "--denovo-position",
        help="position column name used in denovo; " 'defaults to "pos"',
        default="pos",
        action="store",
    )
    parser.add_argument(
        "--skip-columns",
        help="Comma separated columns from denovo to skip",
        default=None,
        action="store",
    )
    parser.add_argument(
        "--sort-order",
        help="Order for sorting variants",
        default=None,
        action="store",
    )

    return parser


class DenovoToVcf:
    """Convert denovo to vcf."""

    def __init__(
        self,
        pedigree_file,
        denovo_file,
        vcf_file,
        pedigree_personId,
        denovo_personId,
        pedigree_delimiter,
        denovo_delimiter,
    ):
        self.pedigree_personId = pedigree_personId
        self.denovo_personId = denovo_personId
        self.pedigree_delimiter = pedigree_delimiter
        self.denovo_delimiter = denovo_delimiter
        self.peopleIds = self.get_peopleIds(pedigree_file)

        self.input_filename = denovo_file
        self.output_filename = vcf_file

    def get_peopleIds(self, pedigree_file):
        pedigree = pd.read_csv(
            pedigree_file, delimiter=self.pedigree_delimiter
        )
        peopleIds = list(pedigree[self.pedigree_personId].values)

        return peopleIds

    def convert(self, chromosome, position, skip_columns=None, sort_order=None):
        """Convert variants at specified chromosome and position."""
        skip_columns = skip_columns or []
        sort_order = sort_order or []
        if self.denovo_personId not in skip_columns:
            skip_columns.append(self.denovo_personId)
        with open(self.input_filename, "r") as input_file:
            reader = csv.DictReader(
                input_file, delimiter=self.denovo_delimiter
            )

            fieldnames = [
                fieldname
                for fieldname in reader.fieldnames
                if fieldname not in skip_columns
            ] + self.peopleIds

            fieldnames.remove("FILTER")

            fieldnames = (
                fieldnames[:5]
                + ["QUAL", "FILTER", "INFO", "FORMAT"]
                + fieldnames[5:]
            )

            vcf_list = []

            for row in reader:
                row_copy = row.copy()

                row_copy.update({"QUAL": ".", "INFO": ".", "FORMAT": "GT"})
                row_copy.update(
                    {personId: "0/0" for personId in self.peopleIds}
                )
                row_copy[row_copy[self.denovo_personId]] = "0/1"

                for key_to_del in skip_columns:
                    row_copy.pop(key_to_del, None)

                vcf_list.append(row_copy)

            vcf = pd.DataFrame(vcf_list, columns=fieldnames)

            vcf.loc[vcf[chromosome] == "X", chromosome] = "23"
            vcf.loc[vcf[chromosome] == "Y", chromosome] = "24"
            vcf[chromosome] = pd.to_numeric(vcf[chromosome])
            vcf[position] = pd.to_numeric(vcf[position])
            vcf = vcf.sort_values(by=sort_order)
            vcf.loc[vcf[chromosome] == 23, chromosome] = "X"
            vcf.loc[vcf[chromosome] == 24, chromosome] = "Y"

            vcf.to_csv(self.output_filename, sep="\t", index=False)


def main():
    """Entry point for the converter."""
    parser = get_argument_parser()
    args = parser.parse_args()

    skip_columns = args.skip_columns
    if skip_columns is None:
        skip_columns = []
    else:
        skip_columns = skip_columns.split(",")

    sort_order = args.sort_order
    if sort_order is None:
        sort_order = []
    else:
        sort_order = sort_order.split(",")

    converter = DenovoToVcf(
        args.pedigree,
        args.denovo,
        args.out,
        args.pedigree_personId,
        args.denovo_personId,
        args.pedigree_delimiter,
        args.denovo_delimiter,
    )
    converter.convert(
        args.denovo_chromosome, args.denovo_position, skip_columns, sort_order
    )


if __name__ == "__main__":
    main()
