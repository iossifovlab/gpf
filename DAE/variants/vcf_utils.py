'''
Created on Mar 5, 2018

@author: lubo
'''
from __future__ import print_function

from builtins import zip
from builtins import str
from builtins import range
import numpy as np


GENOTYPE_TYPE = np.int8


def mat2str(mat, col_sep="", row_sep="/"):
    return row_sep.join([
        col_sep.join(
            [str(n) if n >= 0 else "?" for n in mat[i, :]]
        )
        for i in range(mat.shape[0])])


def str2mat(mat, col_sep="", row_sep="/"):
    if col_sep == "":
        return np.array(
            [[int(c) for c in r]
             for r in mat.split(row_sep)], dtype=GENOTYPE_TYPE)
    return np.array(
        [[int(v) for v in r.split(col_sep)]
         for r in mat.split(row_sep)], dtype=GENOTYPE_TYPE)


def best2gt(mat):
    rows, cols = mat.shape
    res = np.zeros(shape=(2, cols), dtype=GENOTYPE_TYPE)
    for allele_index in range(rows):
        row = mat[allele_index, :]
        for col in range(cols):
            if row[col] == 2:
                res[:, col] = allele_index
            elif row[col] == 1:
                res[0, col] = allele_index

    return res


def reference_genotype(size):
    return np.zeros(shape=(2, size), dtype=GENOTYPE_TYPE)


def trim_str(pos, ref, alt):
    for n, s in enumerate(zip(ref, alt)):
        if s[0] != s[1]:
            break

    if ref[n] == alt[n]:
        ref = ref[n + 1:]
        alt = alt[n + 1:]
        pos += (n + 1)
    else:
        ref = ref[n:]
        alt = alt[n:]
        pos += n

    if len(ref) == 0 or len(alt) == 0:
        return pos, ref, alt

    for n, s in enumerate(zip(ref[::-1], alt[::-1])):
        if s[0] != s[1]:
            break
    # not made simple
    if ref[-(n + 1)] == alt[-(n + 1)]:
        r, a = ref[:-(n + 1)], alt[:-(n + 1)]
    else:
        if n == 0:
            r, a = ref[:], alt[:]
        else:
            r, a = ref[:-n], alt[:-n]
    if len(r) == 0 or len(a) == 0:
        return pos, r, a

    return pos, r, a


def cshl_format(pos, ref, alt):
    p, r, a = trim_str(pos, ref, alt)
    if len(r) == len(a) and len(r) == 0:
        # print('ref {:s} is the same as alt {:s}'.format(
        #     ref, alt), file=sys.stderr)
        return p, 'complex(' + r + '->' + a + ')', 0

    if len(r) == len(a) and len(r) == 1:
        wx = 'sub(' + r + '->' + a + ')'
        return p, wx, 1

    if len(r) > len(a) and len(a) == 0:
        wx = 'del(' + str(len(r)) + ')'
        return p, wx, len(r)

    # len(ref) < len(alt):
    if len(r) < len(a) and len(r) == 0:
        wx = 'ins(' + a + ')'
        return p, wx, len(a)

    return p, 'complex(' + r + '->' + a + ')', max(len(r), len(a))


def vcf2cshl(pos, ref, alt):
    vp, vt, vl = cshl_format(pos, ref, alt)

    return vp, vt, vl
