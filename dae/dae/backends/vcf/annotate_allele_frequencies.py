'''
Created on Mar 5, 2018

@author: lubo
'''
import pandas as pd
import numpy as np


class VcfAnnotatorBase(object):

    def columns(self):
        return self.COLUMNS

    def annotate_variant(self, vcf_variant):
        raise NotImplementedError()

    def annotate_variant_allele(self, allele):
        raise NotImplementedError()

    def annotate(self, annot_df):
        columns = [
            pd.Series(index=annot_df.index, dtype=np.object_)
            for _ in self.columns()
        ]

        for index, allele in enumerate(annot_df.to_dict(orient='records')):
            res = self.annotate_variant_allele(allele)
            for col, _ in enumerate(self.columns()):
                columns[col].iloc[index] = res[col]

        for col, name in enumerate(self.columns()):
            annot_df[name] = columns[col]

        return annot_df


class VcfAlleleFrequencyAnnotator(VcfAnnotatorBase):
    COLUMNS = [
        'af_parents_called_count',
        'af_parents_called_percent',
        'af_allele_count',
        'af_allele_freq',
    ]

    def __init__(self, families, vcf):
        super(VcfAlleleFrequencyAnnotator, self).__init__()
        # self.family_variants = None
        self.families = families
        self.vcf = vcf

        self.independent = self.families.persons_without_parents()
        self.independent_index = \
            np.array(sorted([p.sample_index for p in self.independent]))
        self.n_independent_parents = len(self.independent)

    def get_vcf_variant(self, allele):
        return self.vcf.vars[allele['summary_variant_index']]

    def get_variant_full_genotype(self, allele):
        vcf_variant = self.get_vcf_variant(allele)
        # gt = vcf_variant.gt_idxs[
        #     samples_to_alleles_index(self.independent_index)]
        # gt = gt.reshape([2, len(self.independent_index)], order='F')

        gt = vcf_variant.gt
        gt = gt[:, self.independent_index]

        unknown = np.any(gt == -1, axis=0)
        gt = gt[:, np.logical_not(unknown)]

        return gt

    def annotate_variant_allele(self, allele):
        n_independent_parents = self.n_independent_parents

        gt = self.get_variant_full_genotype(allele)

        n_parents_called = gt.shape[1]
        percent_parents_called = \
            (100.0 * n_parents_called) / n_independent_parents

        allele_index = allele['allele_index']
        n_alleles = np.sum(gt == allele_index)
        allele_freq = 0.0
        if n_parents_called > 0:
            allele_freq = \
                (100.0 * n_alleles) / (2.0 * n_parents_called)

        return n_parents_called, percent_parents_called, \
            n_alleles, allele_freq
