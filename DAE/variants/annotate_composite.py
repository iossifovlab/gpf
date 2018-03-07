'''
Created on Mar 7, 2018

@author: lubo
'''
import pandas as pd
import numpy as np


class AnnotatorBase(object):

    def columns(self):
        return self.COLUMNS

    def annotate_variant(self, vcf_variant):
        raise NotImplemented()

    def annotate(self, vars_df, vcf_vars):
        columns = [
            pd.Series(index=vars_df.index, dtype=np.object_)
            for _ in self.columns()
        ]

        for index, v in enumerate(vcf_vars):
            res = self.annotate_variant(v)
            for col, _ in enumerate(self.columns()):
                columns[col][index] = res[col]

        for col, name in enumerate(self.columns()):
            vars_df[name] = columns[col]

        return vars_df


class AnnotatorComposite(AnnotatorBase):

    def __init__(self, annotators):
        self.annotators = annotators
        self._columns = None

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
