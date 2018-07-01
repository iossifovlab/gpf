'''
Created on Feb 8, 2018

@author: lubo
'''
from __future__ import print_function

import numpy as np
import pandas as pd

from variants.loader import RawVariantsLoader
from variants.family import FamiliesBase
from variants.configure import Configure
from variants.attributes_query import role_query, sex_query, \
    inheritance_query,\
    variant_type_query
from variants.family import Family
from variants.variant import SummaryVariantFactory,\
    FamilyVariantBase, FamilyVariantMulti, FamilyAllele


def split_gene_effect(effects):
    result = []
    if not isinstance(effects, str):
        return result
    for ge in effects.split("|"):
        sym, eff = ge.split(":")
        result.append({'sym': sym, 'eff': eff})
    return result


def parse_gene_effect(effect):
    if isinstance(effect, list):
        return [{'eff': eff, 'sym': sym} for (eff, sym) in effect]
    if effect in set(["CNV+", "CNV-", "intergenic"]):
        return [{'eff': effect, 'sym': ""}]

    return split_gene_effect(effect)


def samples_to_alleles_index(samples):
    return np.stack([2 * samples, 2 * samples + 1]). \
        reshape([1, 2 * len(samples)], order='F')[0]


class VcfFamily(Family):

    def __init__(self, family_id, ped_df):
        super(VcfFamily, self).__init__(family_id, ped_df)
        assert 'sampleIndex' in ped_df.columns

        self.samples = self.ped_df['sampleIndex'].values
        self.alleles = samples_to_alleles_index(self.samples)

    def vcf_samples_index(self, person_ids):
        return self.ped_df[
            self.ped_df['personId'].isin(set(person_ids))
        ]['sampleIndex'].values

    def vcf_alleles_index(self, person_ids):
        p = self.vcf_samples_index(person_ids)
        return samples_to_alleles_index(p)


class VariantFactoryMulti(SummaryVariantFactory):

    @staticmethod
    def from_summary_variant(sv, family, gt):
        return [FamilyVariantMulti(sv, family, gt)]

    @staticmethod
    def family_variant_from_vcf(summary_variant, family, vcf):
        assert vcf is not None
        # assert isinstance(family, VcfFamily)

        gt = vcf.gt_idxs[family.alleles]
        gt = gt.reshape([2, len(family)], order='F')

        return VariantFactoryMulti.from_summary_variant(
            summary_variant, family, gt)

    @staticmethod
    def family_variant_from_gt(summary_variant, family, gt):
        return VariantFactoryMulti.from_summary_variant(
            summary_variant, family, gt=gt)


# class VariantFactorySingle(SummaryVariantFactory):
#
#     @staticmethod
#     def from_summary_variant(
#             summary_variant, family, gt):
#         assert isinstance(family, VcfFamily)
#
#         return [
#             FamilyAllele(summary_allele, family, gt)
#             for summary_allele in summary_variant.alleles
#         ]
#
#     @staticmethod
#     def family_variant_from_vcf(summary_variant, family, vcf):
#         # assert isinstance(family, VcfFamily)
#
#         assert vcf is not None
#         gt = vcf.gt_idxs[family.alleles]
#         gt = gt.reshape([2, len(family)], order='F')
#
#         return VariantFactorySingle.from_summary_variant(
#             summary_variant, family, gt)
#
#     @staticmethod
#     def family_variant_from_gt(summary_variant, family, gt):
#         return VariantFactorySingle.from_summary_variant(
#             summary_variant, family, gt=gt)


class RawFamilyVariants(FamiliesBase):

    def __init__(self, config=None, prefix=None, annotator=None, region=None,
                 variant_factory=VariantFactoryMulti):
        super(RawFamilyVariants, self).__init__()
        if prefix is not None:
            config = Configure.from_prefix_vcf(prefix)

        assert isinstance(config, Configure)

        self.config = config.vcf
        assert self.config is not None

        self.VF = variant_factory
        self._load(annotator, region)

    def is_empty(self):
        return len(self.annot_df) == 0

    def _match_pedigree_to_samples(self, ped_df, samples):
        samples = list(samples)
        samples_needed = set(samples)
        pedigree_samples = set(ped_df['sampleId'].values)
        missing_samples = samples_needed.difference(pedigree_samples)

        samples_needed = samples_needed.difference(missing_samples)
        assert samples_needed.issubset(pedigree_samples)

        pedigree = []
        seen = set()
        for record in ped_df.to_dict(orient='record'):
            if record['sampleId'] in samples_needed:
                if record['sampleId'] in seen:
                    continue
                record['sampleIndex'] = samples.index(record['sampleId'])
                pedigree.append(record)
                seen.add(record['sampleId'])

        assert len(pedigree) == len(samples_needed)

        pedigree_order = list(ped_df['sampleId'].values)
        pedigree = sorted(
            pedigree, key=lambda p: pedigree_order.index(p['sampleId']))

        ped_df = pd.DataFrame(pedigree)
        return ped_df, ped_df['sampleId'].values

    def _load(self, annotator, region):
        loader = RawVariantsLoader(self.config)
        self.ped_df = loader.load_pedigree()

        self.vcf = loader.load_vcf(region)

        self.ped_df, self.samples = self._match_pedigree_to_samples(
            self.ped_df, self.vcf.samples)
        self.families_build(self.ped_df, family_class=VcfFamily)
        assert np.all(self.samples == self.ped_df['sampleId'].values)

        self.vcf_vars = self.vcf.vars

        if annotator is None:
            self.annot_df = loader.load_annotation()
        else:
            records = []
            for index, v in enumerate(self.vcf_vars):
                split = len(v.ALT) > 1
                records.append(
                    (v.CHROM, v.start + 1,
                     v.REF, None,
                     index, split, 0))
                for allele_index, alt in enumerate(v.ALT):
                    records.append(
                        (v.CHROM, v.start + 1,
                         v.REF, alt,
                         index, split, allele_index + 1))
            self.annot_df = pd.DataFrame.from_records(
                data=records,
                columns=[
                    'chrom', 'position', 'reference', 'alternative',
                    'summary_index', 'split_from_multi_allelic',
                    'allele_index'])

            annotator.setup(self)
            self.annot_df = annotator.annotate(self.annot_df, self.vcf_vars)


#  FIXME:
#         assert len(self.annot_df) == len(self.vcf_vars)
#         assert np.all(self.annot_df.index.values ==
#                       np.arange(len(self.annot_df)))

    def persons_samples(self, persons):
        return sorted([p.get_attr('sampleIndex') for p in persons])

    def filter_regions(self, v, regions):
        for reg in regions:
            if reg.chr == v.chromosome and \
                    reg.start <= v.position <= reg.stop:
                return True
        return False

    @staticmethod
    def filter_real_attr(v, real_attr_filter):
        for key, ranges in real_attr_filter.items():
            if not v.has_attribute(key):
                return False

            for sa in v.alt_alleles:
                val = sa.get_attribute(key)
                if val is None:
                    continue
                result = [
                    (val >= rmin) and (val <= rmax) for (rmin, rmax) in ranges
                ]
                if any(result):
                    return True

        return False

    @staticmethod
    def filter_gene_effects(v, effect_types, genes):
        assert effect_types is not None or genes is not None
        if v.effects is None:
            return False

        for effect in v.effects:
            gene_effects = effect.genes

            if effect_types is None:
                result = [
                    ge for ge in gene_effects if ge.symbol in genes]
                if result:
                    return True
            elif genes is None:
                result = [
                    ge for ge in gene_effects if ge.effect in effect_types]
                if result:
                    return True
            else:
                result = [
                    ge for ge in gene_effects
                    if ge.effect in effect_types and ge.symbol in genes]
                if result:
                    return True
        return False

    def filter_allele(self, v, **kwargs):
        if 'regions' in kwargs:
            if not self.filter_regions(v, kwargs['regions']):
                return False
        if 'genes' in kwargs or 'effect_types' in kwargs:
            if not self.filter_gene_effects(
                    v, kwargs.get('effect_types'), kwargs.get('genes')):
                return False
        if 'person_ids' in kwargs:
            person_ids = kwargs['person_ids']
            if not v.variant_in_members & set(person_ids):
                return False
        if 'family_ids' in kwargs and kwargs['family_ids'] is not None:
            family_ids = kwargs['family_ids']
            if v.family_id not in family_ids:
                return False
        if 'roles' in kwargs:
            query = kwargs['roles']
            if not query.match(v.variant_in_roles):
                return False
        if 'sexes' in kwargs:
            query = kwargs['sexes']
            if not query.match(v.variant_in_sexes):
                return False
        if 'variant_type' in kwargs:
            query = kwargs['variant_type']
            if v.details is None:
                return False
            if not query.match(
                    [ad.variant_type for ad in v.details]):
                return False

        if 'real_attr_filter' in kwargs:
            if not self.filter_real_attr(v, kwargs['real_attr_filter']):
                return False
        return True

    def filter_variant(self, v, **kwargs):
        if 'regions' in kwargs:
            if not self.filter_regions(v, kwargs['regions']):
                return False
        if 'inheritance' in kwargs:
            query = kwargs['inheritance']
            if not query.match([v.inheritance]):
                return False
        if 'filter' in kwargs:
            func = kwargs['filter']
            if not func(v):
                return False
        return True

    def query_variants(self, **kwargs):
        annot_df = self.annot_df
        vs = self.wrap_variants(annot_df)

        if 'roles' in kwargs:
            parsed = kwargs['roles']
            if isinstance(parsed, str):
                parsed = role_query.transform_query_string_to_tree(parsed)

            kwargs['roles'] = role_query.transform_tree_to_matcher(parsed)

        if 'sexes' in kwargs:
            parsed = kwargs['sexes']
            if isinstance(parsed, str):
                parsed = sex_query.transform_query_string_to_tree(parsed)

            kwargs['sexes'] = sex_query.transform_tree_to_matcher(parsed)

        if 'inheritance' in kwargs:
            parsed = kwargs['inheritance']
            if isinstance(parsed, str):
                parsed = inheritance_query.transform_query_string_to_tree(
                    parsed)

            kwargs['inheritance'] = inheritance_query.\
                transform_tree_to_matcher(parsed)

        if 'variant_type' in kwargs:
            parsed = kwargs['variant_type']
            if isinstance(kwargs['variant_type'], str):
                parsed = variant_type_query.transform_query_string_to_tree(
                    parsed)

            kwargs['variant_type'] = variant_type_query.\
                transform_tree_to_matcher(parsed)

        for v in vs:
            if not self.filter_variant(v, **kwargs):
                continue
            for va in v:
                if self.filter_allele(va, **kwargs):
                    yield v
                    break

    def wrap_variants(self, annot_df):
        if annot_df is None:
            raise StopIteration()

        variants = self.vcf_vars
        for summary_index, group_df in annot_df.groupby(["summary_index"]):
            vcf = variants[summary_index]
            summary_variant = self.VF.summary_variant_from_records(
                group_df.to_dict(orient='records'))

            for fam in self.families.values():
                vs = self.VF.family_variant_from_vcf(
                    summary_variant, fam, vcf=vcf)
                for v in vs:
                    yield v
