'''
Created on Mar 5, 2018

@author: lubo
'''
import numpy as np


GENOTYPE_TYPE = np.int8
BEST_STATE_TYPE = np.int8


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


def is_reference_genotype(gt):
    return np.any(gt == 0) and \
        np.all(np.logical_or(gt == 0, gt == -1))


def is_all_reference_genotype(gt):
    return np.all(gt == 0)


def is_unknown_genotype(gt):
    return np.any(gt == -1)


def is_all_unknown_genotype(gt):
    return np.all(gt == -1)


def trim_str_front(pos, ref, alt):
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


def trim_str_back(pos, ref, alt):
    assert alt
    assert ref

    for n, s in enumerate(zip(ref[::-1], alt[::-1])):
        if s[0] != s[1]:
            break
    # not made simple
    if ref[-(n+1)] == alt[-(n+1)]:
        r, a = ref[:-(n+1)], alt[:-(n+1)]
    else:
        if n == 0:
            r, a = ref[:], alt[:]
        else:
            r, a = ref[:-n], alt[:-n]

    if len(r) == 0 or len(a) == 0:
        return pos, r, a

    for n, s in enumerate(zip(r, a)):
        if s[0] != s[1]:
            break

    if r[n] == a[n]:
        return pos+n+1, r[n+1:], a[n+1:]

    return pos+n, r[n:], a[n:]


def cshl_format(pos, ref, alt, trimmer=trim_str_front):
    p, r, a = trimmer(pos, ref, alt)
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


def vcf2cshl(pos, ref, alt, trimmer=trim_str_front):
    vp, vt, vl = cshl_format(pos, ref, alt, trimmer=trimmer)

    return vp, vt, vl
