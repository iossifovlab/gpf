'''
Created on Jun 7, 2018

@author: lubo
'''
from __future__ import print_function

import numpy as np
import pandas as pd

from variants.family import FamiliesBase, Family
from variants.variant import SummaryVariantFactory, FamilyVariant,\
    FamilyVariantMulti


class FamilyVariantFactory(object):

    @staticmethod
    def family_variant_from_record(record):
        pass


class DfFamilyVariants(FamiliesBase):

    def __init__(self, ped_df, summary_df, vars_df):
        super(DfFamilyVariants, self).__init__()
        self.summary_df = summary_df
        self.vars_df = vars_df
        self.ped_df = ped_df

        self.families_build(self.ped_df, family_class=Family)

    def filter_regions(self, sdf, vdf, regions):
        def f(df, region):
            return df[np.logical_and(
                df.chrom == region.chr,
                np.logical_and(
                    df.position >= region.start,
                    df.position <= region.stop))
            ]
        sdfs = []
        vdfs = []
        for reg in regions:
            sdfs.append(f(sdf, reg))
            vdfs.append(f(vdf, reg))
        assert len(sdfs) == len(vdfs)
        if len(sdfs) == 0:
            return None, None
        elif len(sdfs) == 1:
            return sdfs[0], vdfs[0]
        else:
            return pd.concat(sdfs), pd.concat(vdfs)

    def filter_families(self, sdf, vdf, family_ids):
        if family_ids is None:
            return sdf, vdf
        vdf = vdf[vdf.family_id.isin(set(family_ids))]
        return sdf, vdf

    def wrap_family_variant(self, record):
        sv = SummaryVariantFactory.summary_variant_from_records([record])
        family = self.families[record['family_id']]
        gt = record['genotype']
        alt_allele_index = record['allele_index']
        return FamilyVariant(sv, family, gt, alt_allele_index)

    @staticmethod
    def merge_genotypes(genotypes):
        if len(genotypes) == 1:
            gt = genotypes[0]
        else:
            genotypes = np.stack(genotypes, axis=0)
            gt = genotypes[0, :]
            unknown_col = np.any(genotypes == -1,  axis=0)

            for index, col in enumerate(unknown_col):
                if not col:
                    continue
                gt[index] = genotypes[genotypes[:, index] != -1, index][0]

        flen = int(len(gt) / 2)
        assert 2 * flen == len(gt)

        gt = gt.reshape([2, flen], order='F')
        return gt

    def wrap_family_variant_multi(self, records):
        sv = SummaryVariantFactory.summary_variant_from_records(records)

        family_id = records[0]['family_id']
        assert all([r['family_id'] == family_id for r in records])

        family = self.families[family_id]
        gt = self.merge_genotypes([r['genotype'] for r in records])

        return FamilyVariantMulti(sv, family, gt)

    def query_variants(self, **kwargs):
        sdf = self.summary_df
        vdf = self.vars_df

        if 'regions' in kwargs and kwargs['regions'] is not None:
            sdf, vdf = self.filter_regions(sdf, vdf, kwargs["regions"])
        if 'family_ids' in kwargs and kwargs['family_ids'] is not None:
            sdf, vdf = self.filter_families(sdf, vdf, kwargs['family_ids'])

        # sdf = sdf.set_index(["var_index", "allele_index"])
        jdf = vdf.join(sdf, on="var_index", rsuffix="_fv")

        print(jdf.columns)
        print("_________________________________________________________")
        print(sdf[["alternative"]])
        print(vdf[["alternative"]])
        print(jdf[["reference", "reference_fv",
                   "alternative", "alternative_fv"]])
        print("_________________________________________________________")

        for _name, group in jdf.groupby(by=["var_index", "family_id"]):
            rec = group.to_dict(orient='records')
            yield self.wrap_family_variant_multi(rec)
