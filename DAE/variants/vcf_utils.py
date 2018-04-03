'''
Created on Mar 5, 2018

@author: lubo
'''
from __future__ import print_function

import numpy as np
from itertools import izip


def samples_to_alleles_index(samples):
    return np.stack([2 * samples, 2 * samples + 1]). \
        reshape([1, 2 * len(samples)], order='F')[0]


def mat2str(mat, col_sep="", row_sep="/"):
    return row_sep.join([
        col_sep.join(
            [str(n) if n >= 0 else "?" for n in mat[i, :]]
        )
        for i in xrange(mat.shape[0])])


def trim_str(pos, ref, alt):
    for n, s in enumerate(izip(ref, alt)):
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

    for n, s in enumerate(izip(ref[::-1], alt[::-1])):
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


def vcf2cshl(pos, ref, alts):
    vrt, pxx, lens = list(), list(), list()
    for alt in alts:
        p, vt, vl = cshl_format(pos, ref, alt)

        pxx.append(p)
        vrt.append(vt)
        lens.append(vl)

    return pxx, vrt, lens
