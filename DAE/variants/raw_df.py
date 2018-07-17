'''
Created on Jun 7, 2018

@author: lubo
'''
from __future__ import print_function

import numpy as np
import pandas as pd

from variants.family import FamiliesBase, Family
from variants.variant import SummaryVariantFactory
from variants.attributes import Inheritance, Role, Sex
from variants.attributes_query import role_query, inheritance_query, sex_query
from variants.family_variant import FamilyVariant


class FamilyVariantFactory(object):

    @staticmethod
    def family_variant_from_record(record):
        pass


class DfFamilyVariantsBase(object):

    @staticmethod
    def wrap_family_variant_multi(families, records):
        sv = SummaryVariantFactory.summary_variant_from_records(records)

        family_id = records[0]['family_id']
        assert all([r['family_id'] == family_id for r in records])

        family = families[family_id]
        gt = records[0]['genotype']
        gt = gt.reshape([2, len(family)], order='F')

        return FamilyVariant(sv, family, gt)

    @staticmethod
    def wrap_variants(families, join_df):
        join_df = join_df.sort_values(
            by=["summary_index", "family_id", "allele_index"])

        for _name, group in join_df.groupby(by=["summary_index", "family_id"]):
            rec = group.to_dict(orient='records')
            yield DfFamilyVariantsBase.wrap_family_variant_multi(families, rec)


class DfFamilyVariants(FamiliesBase, DfFamilyVariantsBase):

    def __init__(self, ped_df, summary_df, vars_df, f2s_df):
        super(DfFamilyVariants, self).__init__()
        self.summary_df = summary_df
        self.vars_df = vars_df
        self.f2s_df = f2s_df
        self.ped_df = ped_df

        self.families_build(self.ped_df, family_class=Family)

    @staticmethod
    def filter_regions(sdf, vdf, regions):
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

    @staticmethod
    def filter_families(sdf, vdf, family_ids):
        if family_ids is None:
            return sdf, vdf
        vdf = vdf[vdf.family_id.isin(set(family_ids))]
        return sdf, vdf

    @staticmethod
    def filter_roles(sdf, vdf, roles):
        si = set(vdf[vdf.variant_in_roles
                     .apply(lambda r: map(Role, r))
                     .apply(roles)].summary_index.values)
        vdf = vdf[vdf.summary_index.isin(si)]
        sdf = sdf[sdf.summary_index.isin(si)]
        return sdf, vdf

    @staticmethod
    def filter_sexes(sdf, vdf, sexes):
        si = set(vdf[vdf.variant_in_sexes
                     .apply(lambda v: map(Sex, v))
                     .apply(sexes)].summary_index.values)
        vdf = vdf[vdf.summary_index.isin(si)]
        sdf = sdf[sdf.summary_index.isin(si)]
        return sdf, vdf

    @staticmethod
    def filter_inheritance(sdf, vdf, inheritance):
        si = set(vdf[vdf.inheritance
                     .apply(lambda v: Inheritance(v))
                     .apply(inheritance)].summary_index.values)
        vdf = vdf[vdf.summary_index.isin(si)]
        sdf = sdf[sdf.summary_index.isin(si)]
        return sdf, vdf

    def query_variants(self, **kwargs):
        sdf = self.summary_df
        vdf = self.vars_df

        if 'regions' in kwargs and kwargs['regions'] is not None:
            sdf, vdf = self.filter_regions(sdf, vdf, kwargs["regions"])
        if 'family_ids' in kwargs and kwargs['family_ids'] is not None:
            sdf, vdf = self.filter_families(sdf, vdf, kwargs['family_ids'])
        if kwargs.get('roles') is not None:
            query = kwargs.get('roles')
            assert isinstance(query, str)

            query = role_query.transform_tree_to_matcher(
                role_query.transform_query_string_to_tree(query))
            sdf, vdf = self.filter_roles(
                sdf, vdf, lambda v: query.match(v))

        if kwargs.get('sexes') is not None:
            query = kwargs.get('sexes')
            assert isinstance(query, str)

            query = sex_query.transform_tree_to_matcher(
                sex_query.transform_query_string_to_tree(query))
            sdf, vdf = self.filter_sexes(
                sdf, vdf, lambda v: query.match(v))

        if kwargs.get('inheritance') is not None:
            query = kwargs.get('inheritance')
            assert isinstance(query, str)

            query = inheritance_query.transform_tree_to_matcher(
                inheritance_query.transform_query_string_to_tree(query))
            sdf, vdf = self.filter_inheritance(
                sdf, vdf, lambda v: query.match([v]))

        join_df = pd.merge(sdf, vdf,
                           on=['summary_index'],
                           how='outer',
                           suffixes=('', '_fv'),
                           sort=True)

        return self.wrap_variants(self.families, join_df)
