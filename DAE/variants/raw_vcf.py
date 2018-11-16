'''
Created on Feb 8, 2018

@author: lubo
'''
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str

import numpy as np
import pandas as pd

from variants.loader import RawVariantsLoader
from variants.family import FamiliesBase
from variants.configure import Configure
from variants.attributes_query import role_query, sex_query, \
    inheritance_query,\
    variant_type_query
from variants.family import Family
from variants.variant import SummaryVariantFactory
from variants.family_variant import FamilyVariant, FamilyAllele
import os


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


class VariantFactory(SummaryVariantFactory):

    @staticmethod
    def from_summary_variant(sv, family, gt):
        return FamilyVariant(sv, family, gt)

    @staticmethod
    def family_variant_from_vcf(summary_variant, family, vcf):
        assert vcf is not None
        # assert isinstance(family, VcfFamily)

        gt = np.copy(vcf.gt_idxs[family.alleles])
        gt = gt.reshape([2, len(family)], order='F')

        return VariantFactory.from_summary_variant(
            summary_variant, family, gt)

    @staticmethod
    def family_variant_from_gt(summary_variant, family, gt):
        return VariantFactory.from_summary_variant(
            summary_variant, family, gt=gt)


class RawFamilyVariants(FamiliesBase):

    def __init__(self, config=None, prefix=None, annotator=None, region=None,
                 variant_factory=VariantFactory):
        super(RawFamilyVariants, self).__init__()
        if prefix is not None:
            config = Configure.from_prefix_vcf(prefix)

        assert isinstance(config, Configure)

        self.config = config.vcf
        assert self.config is not None

        self.VF = variant_factory
        self.prefix = prefix
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

    def _load_pedigree(self):
        assert self.config.pedigree
        assert os.path.exists(self.config.pedigree), self.config.pedigree

        return FamiliesBase.load_pedigree_file(self.config.pedigree)

    def _load(self, annotator, region):
        loader = RawVariantsLoader(self.config)
        self.ped_df = self._load_pedigree()

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
                allele_count = len(v.ALT) + 1
                records.append(
                    (v.CHROM, v.start + 1,
                     v.REF, None,
                     index, 0, allele_count))
                for allele_index, alt in enumerate(v.ALT):
                    records.append(
                        (v.CHROM, v.start + 1,
                         v.REF, alt,
                         index,
                         allele_index + 1, allele_count
                         ))
            self.annot_df = pd.DataFrame.from_records(
                data=records,
                columns=[
                    'chrom', 'position', 'reference', 'alternative',
                    'summary_variant_index',
                    'allele_index', 'allele_count',
                ])

            annotator.setup(self)
            self.annot_df = annotator.annotate(self.annot_df)

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
    def filter_real_attr(va, real_attr_filter):
        for key, ranges in list(real_attr_filter.items()):
            if not va.has_attribute(key):
                return False

            val = va.get_attribute(key)
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
        if v.effect is None:
            return False

        gene_effects = v.effect.genes

        if effect_types is None:
            result = [
                ge for ge in gene_effects if ge.symbol in genes]
            if result:
                v.matched_gene_effects = result
                return True
        elif genes is None:
            result = [
                ge for ge in gene_effects if ge.effect in effect_types]
            if result:
                v.matched_gene_effects = result
                return True
        else:
            result = [
                ge for ge in gene_effects
                if ge.effect in effect_types and ge.symbol in genes]
            if result:
                v.matched_gene_effects = result
                return True
        return False

    def filter_allele(self, allele, **kwargs):
        assert isinstance(allele, FamilyAllele)

        if kwargs.get('real_attr_filter') is not None:
            if not self.filter_real_attr(allele, kwargs['real_attr_filter']):
                return False
        if kwargs.get('genes') is not None or \
                kwargs.get('effect_types') is not None:
            if not self.filter_gene_effects(
                    allele, kwargs.get('effect_types'), kwargs.get('genes')):
                return False
        if kwargs.get('variant_type') is not None:
            query = kwargs['variant_type']
            if allele.details is None:
                return False
            if not query.match(
                    [allele.details.variant_type]):
                return False
        if kwargs.get('person_ids') is not None:
            if allele.is_reference_allele:
                return False
            person_ids = kwargs['person_ids']
            if not allele.variant_in_members & set(person_ids):
                return False
        if kwargs.get('roles') is not None:
            if allele.is_reference_allele:
                return False
            query = kwargs['roles']
            if not query.match(allele.variant_in_roles):
                return False
        if kwargs.get('sexes') is not None:
            if allele.is_reference_allele:
                return False
            query = kwargs['sexes']
            if not query.match(allele.variant_in_sexes):
                return False
        if kwargs.get('inheritance') is not None:
            # if v.is_reference_allele:
            #     return False
            query = kwargs['inheritance']
            if not query.match(allele.inheritance_in_members):
                return False
        return True

    def filter_variant(self, v, **kwargs):
        if kwargs.get('regions') is not None:
            if not self.filter_regions(v, kwargs['regions']):
                return False
        if 'family_ids' in kwargs and kwargs['family_ids'] is not None:
            family_ids = kwargs['family_ids']
            if v.family_id not in family_ids:
                return False
        if 'filter' in kwargs:
            func = kwargs['filter']
            if not func(v):
                return False
        if kwargs.get('pedigreeSelector') is not None:
            pd = kwargs.get('pedigreeSelector')
            if len(
                v.variant_in_members -
                set([m.person_id for m in v.family.get_people_with_phenotypes(
                     pd['source'], pd['checkedValues'])])):
                return False
        return True

    def query_variants(self, **kwargs):
        annot_df = self.annot_df

        if kwargs.get("roles") is not None:
            parsed = kwargs['roles']
            if isinstance(parsed, str):
                parsed = role_query.transform_query_string_to_tree(parsed)

            kwargs['roles'] = role_query.transform_tree_to_matcher(parsed)

        if kwargs.get('sexes') is not None:
            parsed = kwargs['sexes']
            if isinstance(parsed, str):
                parsed = sex_query.transform_query_string_to_tree(parsed)

            kwargs['sexes'] = sex_query.transform_tree_to_matcher(parsed)

        if kwargs.get('inheritance') is not None:
            parsed = kwargs['inheritance']
            if isinstance(parsed, str):
                parsed = inheritance_query.transform_query_string_to_tree(
                    parsed)

            kwargs['inheritance'] = inheritance_query.\
                transform_tree_to_matcher(parsed)

        if kwargs.get('variant_type') is not None:
            parsed = kwargs['variant_type']
            if isinstance(kwargs['variant_type'], str):
                parsed = variant_type_query.transform_query_string_to_tree(
                    parsed)

            kwargs['variant_type'] = variant_type_query.\
                transform_tree_to_matcher(parsed)

        vs = self.wrap_variants(annot_df)

        return_reference = kwargs.get("return_reference", False)
        return_unknown = kwargs.get("return_unknown", False)

        for v in vs:
            if v.is_unknown() and not return_unknown:
                continue

            if not self.filter_variant(v, **kwargs):
                continue

            alleles = v.alleles
            alleles_matched = []
            for allele in alleles:
                if self.filter_allele(allele, **kwargs):
                    alleles_matched.append(allele.allele_index)
            if alleles_matched:
                if len(alleles_matched) == 1 and \
                        alleles_matched[0] == 0 and \
                        not return_reference:
                    continue
                v.set_matched_alleles(alleles_matched)
                yield v

    def wrap_variants(self, annot_df):
        if annot_df is None:
            return

        variants = self.vcf_vars
        for summary_index, group_df in \
                annot_df.groupby("summary_variant_index"):
            vcf = variants[summary_index]
            summary_variant = self.VF.summary_variant_from_records(
                group_df.to_dict(orient='records'))

            for fam in list(self.families.values()):
                v = self.VF.family_variant_from_vcf(
                    summary_variant, fam, vcf=vcf)
                yield v
        return
