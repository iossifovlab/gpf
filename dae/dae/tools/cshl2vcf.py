#!/bin/env python
import csv
import sys

from dae.utils.dae_utils import cshl2vcf_variant

if __name__ == "__main__":
    from dae.gpf_instance.gpf_instance import GPFInstance

    gpf_instance = GPFInstance.build()

    GENOME = gpf_instance.reference_genome
    with open(sys.argv[1], "r") as csvfile, open(sys.argv[2], "w") as output:
        reader = csv.DictReader(csvfile, delimiter="\t")
        assert reader.fieldnames is not None
        fieldnames = list(reader.fieldnames)
        fieldnames.extend(["chr", "pos", "ref", "alt"])
        writer = csv.DictWriter(output, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            chromosome, pos, ref, alt = cshl2vcf_variant(
                row["location"], row["variant"], GENOME,
            )
            row["chr"] = chromosome
            row["pos"] = pos
            row["ref"] = ref
            row["alt"] = alt
            print((chromosome, pos, ref, alt))
            writer.writerow(row)
