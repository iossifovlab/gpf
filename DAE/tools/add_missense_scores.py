#!/bin/env python
from DAE import genomesDB
import sys
import csv
from variant_annotation.missense_scores import MissenseScoresDB
from variant_annotation.variant import Variant


if __name__ == "__main__":
    GA = genomesDB.get_genome()
    gmDB = genomesDB.get_gene_models()
    mDB = MissenseScoresDB()
    mDB.load_all_indexes()
    missense_field_names = mDB.get_field_names()

    with open(sys.argv[1], "r") as csvfile, open(sys.argv[2], "w") as output:
        reader = csv.DictReader(csvfile, delimiter='\t')
        fieldnames = reader.fieldnames
        fieldnames.extend(missense_field_names)

        writer = csv.DictWriter(output, delimiter='\t', fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            variant = Variant(loc=row["location"], var=row["variant"])
            if row["effectType"] == "missense":
                missense_scores = mDB.get_missense_score(variant)

                if missense_scores is not None:
                    for name, score in zip(missense_field_names,
                                           missense_scores):
                        row[name] = score
            writer.writerow(row)
