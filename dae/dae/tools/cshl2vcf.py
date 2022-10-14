#!/bin/env python

import re
import sys
import csv


subRE = re.compile(r"^sub\(([ACGT])->([ACGT])\)$")
insRE = re.compile(r"^ins\(([ACGT]+)\)$")
delRE = re.compile(r"^del\((\d+)\)$")


def cshl2vcf(loc, var, genome):
    chrom, pos = loc.split(":")
    pos = int(pos)

    mS = subRE.match(var)
    if mS:
        return chrom, pos, mS.group(1), mS.group(2)

    mI = insRE.match(var)
    if mI:
        sq = mI.group(1)
        rfS = genome.get_sequence(chrom, pos - 1, pos - 1)
        return chrom, pos - 1, rfS, rfS + sq

    mD = delRE.match(var)
    if mD:
        ln = int(mD.group(1))
        rfS = genome.get_sequence(chrom, pos - 1, pos + ln - 1)
        return chrom, pos - 1, rfS, rfS[0]

    raise Exception("weird variant:" + var)


if __name__ == "__main__":
    from dae.gpf_instance.gpf_instance import GPFInstance

    gpf_instance = GPFInstance.build()

    GENOME = gpf_instance.reference_genome
    with open(sys.argv[1], "r") as csvfile, open(sys.argv[2], "w") as output:
        reader = csv.DictReader(csvfile, delimiter="\t")
        fieldnames = list((*reader.fieldnames, "chr", "pos", "ref", "alt"))
        writer = csv.DictWriter(output, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            chromosome, pos, ref, alt = cshl2vcf(
                row["location"], row["variant"], GENOME
            )
            row["chr"] = chromosome
            row["pos"] = pos
            row["ref"] = ref
            row["alt"] = alt
            print((chromosome, pos, ref, alt))
            writer.writerow(row)
