'''
Created on Mar 5, 2018

@author: lubo
'''
from __future__ import unicode_literals
import re

SUB_COMPLEX_RE = re.compile(r'^(sub|complex)\(([NACGT]+)->([NACGT]+)\)$')
INS_RE = re.compile(r'^ins\(([NACGT]+)\)$')
DEL_RE = re.compile(r'^del\((\d+)\)$')


def dae2vcf_variant(chrom, position, var, genome=None):
    if genome is None:
        from DAE import genomesDB
        genome = genomesDB.get_genome()

    match = SUB_COMPLEX_RE.match(var)
    if match:
        return position, match.group(2), match.group(3)

    match = INS_RE.match(var)
    if match:
        alt_suffix = match.group(1)
        reference = genome.getSequence(chrom, position - 1, position - 1)
        return position - 1, reference, reference + alt_suffix

    match = DEL_RE.match(var)
    if match:
        count = int(match.group(1))
        reference = genome.getSequence(
            chrom, position - 1, position + count - 1)
        assert len(reference) == count + 1, reference
        return position - 1, reference, reference[0]

    raise NotImplementedError('weird variant: ' + var)


def split_iterable(iterable, max_chunk_length=5000):
    i = 0
    result = []

    for value in iterable:
        i += 1
        result.append(value)

        if i == max_chunk_length:
            yield result
            result = []
            i = 0

    if i != 0:
        yield result
