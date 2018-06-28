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
from variants.attributes import Inheritance


class FamilyVariantFactory(object):

    @staticmethod
    def family_variant_from_record(record):
        pass


class DfFamilyVariantsBase(object):

    @staticmethod
    def wrap_family_variant(families, record):
        sv = SummaryVariantFactory.summary_variant_from_records([record])
        family = families[record['family_id']]
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

    @staticmethod
    def wrap_family_variant_multi(families, records):
        sv = SummaryVariantFactory.summary_variant_from_records(records)
        print(sv)

        family_id = records[0]['family_id']
        assert all([r['family_id'] == family_id for r in records])

        family = families[family_id]
        gt = DfFamilyVariantsBase.merge_genotypes(
            [r['genotype'] for r in records])

        return FamilyVariantMulti(sv, family, gt)

    @staticmethod
    def wrap_variants(families, join_df):
        print(join_df.head())

        print(join_df.columns)
        print("----------------------------------------------------------")
        print("join_df before sort")
        print(join_df[["var_index", "allele_index", 
                       "reference",
                       "alternative", "alternative_fv",
                       "family_id", "genotype", "inheritance"]])
#         join_df = join_df.sort_values(
#             by=["var_index", "allele_index", "allele_index_fv"])
#         print("----------------------------------------------------------")
#         print("join_df after sort")
#         print(join_df[["var_index", "allele_index", "allele_index_fv",
#                        "reference",
#                        "alternative", "alternative_fv",
#                        "family_id", "genotype", "inheritance"]])
#         print("----------------------------------------------------------")

        for _name, group in join_df.groupby(by=["var_index", "family_id"]):

            if group.inheritance.unique()[0] != Inheritance.reference.value:

                print(group[["var_index", "allele_index",
                             "reference",
                             "alternative", "alternative_fv",
                             "family_id", "genotype", "inheritance"]])
                # group = group.drop_duplicates(
                #     subset=["var_index", "allele_index"])
#                 subset = group.allele_index.max()
#                 group = group.head(subset)
# 
#                 print(group[["var_index", "allele_index", "allele_index_fv",
#                              "reference",
#                              "alternative", "alternative_fv",
#                              "family_id", "genotype", "inheritance"]])
            rec = group.to_dict(orient='records')
            yield DfFamilyVariantsBase.wrap_family_variant_multi(families, rec)


class DfFamilyVariants(FamiliesBase, DfFamilyVariantsBase):

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

    def query_variants(self, **kwargs):
        sdf = self.summary_df
        vdf = self.vars_df

        if 'regions' in kwargs and kwargs['regions'] is not None:
            sdf, vdf = self.filter_regions(sdf, vdf, kwargs["regions"])
        if 'family_ids' in kwargs and kwargs['family_ids'] is not None:
            sdf, vdf = self.filter_families(sdf, vdf, kwargs['family_ids'])

        # sdf = sdf.set_index(["var_index", "allele_index"])
        print("_________________________________________________________")
        print(sdf[["var_index", "allele_index", "alternative"]])
        print(vdf[["var_index", "allele_index", "alternative", "family_id"]])
        print("_________________________________________________________")

        join_df = sdf.join(
            vdf.set_index(['var_index', 'allele_index']),
            on=['var_index', 'allele_index'],
            rsuffix="_fv")
        print(join_df[["var_index", "allele_index",
                       "reference",
                       "alternative", "alternative_fv",
                       "family_id"]])
        print("_________________________________________________________")

        return self.wrap_variants(self.families, join_df)
