'''
Created on Mar 7, 2018

@author: lubo
'''
from __future__ import print_function, absolute_import, unicode_literals

from builtins import object
import pandas as pd
import numpy as np


class AnnotatorBase(object):

    def setup(self, family_variants):
        pass

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

    def annotate_variant_allele(self, allele):
        res = []
        for annot in self.annotators:
            res.extend(annot.annotate_variant_allele(allele))
        return res
