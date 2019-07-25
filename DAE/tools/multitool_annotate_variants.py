#!/bin/env python
from DAE import genomesDB
import sys
import csv
from variant_annotation.multitool.multi_annotator import MultiVariantAnnotator


if __name__ == "__main__":
    GA = genomesDB.get_genome()
    gmDB = genomesDB.get_gene_models()
    annotator = MultiVariantAnnotator(GA, gmDB)

    with open(sys.argv[1], "r") as csvfile, open(sys.argv[2], "w") as output:
        reader = csv.DictReader(csvfile, delimiter='\t')
        fieldnames = reader.fieldnames

        for adapter in annotator.annotators:
            fieldnames.append(adapter.__class__.__name__ + "_effect")
            fieldnames.append(adapter.__class__.__name__ + "_details")
        writer = csv.DictWriter(output, delimiter='\t', fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            res = annotator.annotate_variant(loc=row["location"],
                                             var=row["variant"])
            for adapter_name, result in res:
                print("--------")
                for effect in result:
                    print(("A", effect.effect_type, effect.effect_details))

                effects = [effect.effect_type for effect in result]
                effect_details = [effect.effect_details for effect in result]
                row[adapter_name + "_effect"] = ",".join(effects)
                row[adapter_name + "_details"] = ",".join(effect_details)

            writer.writerow(row)
