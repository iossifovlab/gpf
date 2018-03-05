'''
Created on Mar 5, 2018

@author: lubo
'''
import numpy as np
from variants.family import Family


def samples_to_alleles_index(samples):
    return np.stack([2 * samples, 2 * samples + 1]). \
        reshape([1, 2 * len(samples)], order='F')[0]


def mat2str(mat, col_sep="", row_sep="/"):
    return row_sep.join([
        col_sep.join(
            [str(n) if n >= 0 else "?" for n in mat[i, :]]
        )
        for i in xrange(mat.shape[0])])


class VcfFamily(Family):

    def __init__(self, family_id, ped_df):
        super(VcfFamily, self).__init__(family_id, ped_df)

        self.samples = self.ped_df.index.values
        self.alleles = samples_to_alleles_index(self.samples)

    def vcf_samples_index(self, person_ids):
        return self.ped_df[
            self.ped_df['personId'].isin(set(person_ids))
        ].index.values

    def vcf_alleles_index(self, person_ids):
        p = self.vcf_samples_index(person_ids)
        return samples_to_alleles_index(p)
