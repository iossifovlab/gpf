#!/bin/env python
import csv
from variant_annotation.missense_scores_tabix import MissenseScoresDB
from variant_annotation.variant import Variant
import argparse


if __name__ == "__main__":
    mDB = MissenseScoresDB()

    parser = argparse.ArgumentParser(
        description='Add missense scores from dbSNFP',
        epilog="Supported columns:\n" + '\n'.join(mDB.get_field_names()))
    parser.add_argument('input_file')
    parser.add_argument('output_file')
    parser.add_argument('-c', action='append', default=[], dest="columns",
                        required=True)
    args = parser.parse_args()

    with open(args.input_file, "r") as csvfile, \
            open(args.output_file, "w") as output:
        reader = csv.DictReader(csvfile, delimiter='\t')
        fieldnames = reader.fieldnames
        fieldnames.extend(args.columns)

        writer = csv.DictWriter(output, delimiter='\t', fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            variant = Variant(loc=row["location"], var=row["variant"])
            if row["effectType"] == "missense":
                missense_scores = mDB.get_missense_score(variant)
                if missense_scores is not None:
                    values = {k: missense_scores[k] for k in args.columns}
                    row.update(values)
            writer.writerow(row)
