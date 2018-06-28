'''
Created on Mar 5, 2018

@author: lubo
'''
import re

SUB_COMPLEX_RE = re.compile('^(sub|complex)\(([NACGT]+)->([NACGT]+)\)$')
INS_RE = re.compile('^ins\(([NACGT]+)\)$')
DEL_RE = re.compile('^del\((\d+)\)$')

def dae2vcf_variant(chrom, position, var, GA=None):
    if GA is None:
        from DAE import genomesDB
        GA = genomesDB.get_genome()

    match = SUB_COMPLEX_RE.match(var)
    if match:
        return position, match.group(2), match.group(3)

    match = INS_RE.match(var)
    if match:
        alt_suffix = match.group(1)
        reference = GA.getSequence(chrom, position - 1, position - 1)
        return position - 1, reference, reference + alt_suffix

    match = DEL_RE.match(var)
    if match:
        count = int(match.group(1))
        reference = GA.getSequence(chrom, position - 1, position + count - 1)
        return position - 1, reference, reference[0]

    raise NotImplementedError('weird variant: ' + var)
