'''
Created on Mar 7, 2018

@author: lubo
'''
from __future__ import print_function

import pandas as pd
import numpy as np
import itertools


class AnnotatorBase(object):

    def setup(self, family_variants):
        pass

    def columns(self):
        return self.COLUMNS

    def annotate_variant(self, vcf_variant):
        raise NotImplemented()

    def annotate(self, annot_df, vcf_vars):
        columns = [
            pd.Series(index=annot_df.index, dtype=np.object_)
            for _ in self.columns()
        ]

        index = 0
        for vcf_index, v in enumerate(vcf_vars):
            res = self.annotate_variant(v)
            for allele_index, _ in enumerate(itertools.chain([v.REF], v.ALT)):
                assert annot_df['summary_variant_index'][index] == vcf_index
                assert annot_df['allele_index'][index] == allele_index

                for col, _ in enumerate(self.columns()):
                    columns[col][index] = res[col][allele_index]
                index += 1

        for col, name in enumerate(self.columns()):
            annot_df[name] = columns[col]

        return annot_df


class AnnotatorComposite(AnnotatorBase):

    def __init__(self, annotators):
        self.annotators = annotators
        self._columns = None

    def setup(self, family_variants):
        super(AnnotatorComposite, self).setup(family_variants)

        for annot in self.annotators:
            annot.setup(family_variants)

    def columns(self):
        if self._columns is None:
            self._columns = []
            for annot in self.annotators:
                self._columns.extend(annot.columns())
        return self._columns

    def annotate_variant(self, vcf_variant):
        res = []
        for annot in self.annotators:
            res.extend(annot.annotate_variant(vcf_variant))
        return res
