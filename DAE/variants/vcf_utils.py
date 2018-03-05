'''
Created on Mar 5, 2018

@author: lubo
'''
import numpy as np


def samples_to_alleles_index(samples):
    return np.stack([2 * samples, 2 * samples + 1]). \
        reshape([1, 2 * len(samples)], order='F')[0]


def mat2str(mat, col_sep="", row_sep="/"):
    return row_sep.join([
        col_sep.join(
            [str(n) if n >= 0 else "?" for n in mat[i, :]]
        )
        for i in xrange(mat.shape[0])])
