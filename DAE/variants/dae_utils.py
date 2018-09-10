'''
Created on Mar 5, 2018

@author: lubo
'''
import re

from DAE import genomesDB


GA = genomesDB.get_genome()  # @UndefinedVariable


SUB_RE = re.compile('^sub\(([ACGT])->([ACGT])\)$')
INS_RE = re.compile('^ins\(([ACGT]+)\)$')
DEL_RE = re.compile('^del\((\d+)\)$')


def dae2vcf_variant(chrom, position, var):
    # print(chrom, position, var)

    match = SUB_RE.match(var)
    if match:
        return chrom, position, match.group(1), match.group(2)

    match = INS_RE.match(var)
    if match:
        alt_suffix = match.group(1)
        reference = GA.getSequence(chrom, position - 1, position - 1)
        return chrom, position - 1, reference, reference + alt_suffix

    match = DEL_RE.match(var)
    if match:
        count = int(match.group(1))
        reference = GA.getSequence(chrom, position - 1, position + count - 1)
        return chrom, position - 1, reference, reference[0]

    raise NotImplementedError('weird variant: ' + var)
