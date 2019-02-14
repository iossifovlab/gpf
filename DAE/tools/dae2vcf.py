#!/bin/env python
from __future__ import print_function
from __future__ import unicode_literals
from DAE import genomesDB
import re
import sys
import csv

GA = genomesDB.get_genome()
gmDB = genomesDB.get_gene_models()

subRE = re.compile('^sub\(([ACGT])->([ACGT])\)$')
insRE = re.compile('^ins\(([ACGT]+)\)$')
delRE = re.compile('^del\((\d+)\)$')


def vcfVarFormat(loc, var):
    chr, pos = loc.split(":")
    pos = int(pos)

    mS = subRE.match(var)
    if mS:
        return chr, pos, mS.group(1), mS.group(2)

    mI = insRE.match(var)
    if mI:
        sq = mI.group(1)
        rfS = GA.getSequence(chr, pos-1, pos-1)
        return chr, pos-1, rfS, rfS+sq

    mD = delRE.match(var)
    if mD:
        ln = int(mD.group(1))
        rfS = GA.getSequence(chr, pos - 1, pos + ln - 1)
        return chr, pos-1, rfS, rfS[0]

    raise Exception('weird variant:' + var)


if __name__ == "__main__":
    with open(sys.argv[1], "r") as csvfile, open(sys.argv[2], "w") as output:
        reader = csv.DictReader(csvfile, delimiter='\t')
        fieldnames = reader.fieldnames
        fieldnames.extend(["chr", "pos", "ref", "alt"])
        writer = csv.DictWriter(output, delimiter='\t', fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            chromosome, pos, ref, alt = vcfVarFormat(row["location"],
                                                     row["variant"])
            row["chr"] = chromosome
            row["pos"] = pos
            row["ref"] = ref
            row["alt"] = alt
            print((chromosome, pos, ref, alt))
            writer.writerow(row)
