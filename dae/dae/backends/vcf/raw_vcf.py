import os

import numpy as np
import pandas as pd

from dae.pedigrees.pedigree_reader import PedigreeReader

from dae.variants.family import FamiliesBase
from dae.variants.family import Family
from dae.variants.variant import SummaryVariantFactory
from dae.variants.family_variant import FamilyVariant, FamilyAllele

from dae.backends.vcf.loader import RawVariantsLoader
from dae.backends.configure import Configure
from dae.backends.attributes_query import role_query, sex_query, \
    inheritance_query,\
    variant_type_query


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


# def samples_to_alleles_index(samples):
#     return np.stack([2 * samples, 2 * samples + 1]). \
#         reshape([1, 2 * len(samples)], order='F')[0]


class VcfFamily(Family):

    @classmethod
    def from_df(cls, family_id, ped_df):
        assert 'sampleIndex' in ped_df.columns
        family = Family.from_df(family_id, ped_df)

        family.samples = ped_df['sampleIndex'].values

        return family

    def __init__(self, family_id):
        super(VcfFamily, self).__init__(family_id)
        self.samples = []
        self.alleles = []

    def vcf_samples_index(self, person_ids):
        return self.ped_df[
            self.ped_df['personId'].isin(set(person_ids))
        ]['sampleIndex'].values


class VariantFactory(SummaryVariantFactory):

    @staticmethod
    def from_summary_variant(sv, family, gt):
        return FamilyVariant.from_sumary_variant(sv, family, gt)

    @staticmethod
    def family_variant_from_vcf(summary_variant, family, vcf):
        assert vcf is not None
        # assert isinstance(family, VcfFamily)

        # gt = vcf.gt_idxs[family.alleles].\
        #     astype(GENOTYPE_TYPE, casting='same_kind')
        # gt = gt.reshape([2, len(family)], order='F')

        gt = vcf.gt[:, family.samples]
        assert gt.shape == (2, len(family))

        return VariantFactory.from_summary_variant(
            summary_variant, family, gt)


class RawFamilyVariants(FamiliesBase):

    def __init__(self, config=None, prefix=None, annotator=None, region=None,
                 transmission_type='transmitted',
                 variant_factory=VariantFactory, genomes_db=None):
        super(RawFamilyVariants, self).__init__()
        if prefix is not None:
            config = Configure.from_prefix_vcf(prefix)

        assert isinstance(config, Configure)

        self.config = config.vcf
        assert self.config is not None

        self.VF = variant_factory
        self.prefix = prefix
        self.transmission_type = transmission_type

        self._load(annotator, region, genomes_db)

    def is_empty(self):
        return len(self.annot_df) == 0

    def _match_pedigree_to_samples(self, ped_df, samples):
        samples = list(samples)
        samples_needed = set(samples)
        pedigree_samples = set(ped_df['sample_id'].values)
        missing_samples = samples_needed.difference(pedigree_samples)

        samples_needed = samples_needed.difference(missing_samples)
        assert samples_needed.issubset(pedigree_samples)

        pedigree = []
        seen = set()
        for record in ped_df.to_dict(orient='record'):
            if record['sample_id'] in samples_needed:
                if record['sample_id'] in seen:
                    continue
                record['sampleIndex'] = samples.index(record['sample_id'])
                pedigree.append(record)
                seen.add(record['sample_id'])

        assert len(pedigree) == len(samples_needed)

        pedigree_order = list(ped_df['sample_id'].values)
        pedigree = sorted(
            pedigree, key=lambda p: pedigree_order.index(p['sample_id']))

        ped_df = pd.DataFrame(pedigree)
        return ped_df, ped_df['sample_id'].values

    def _load_pedigree(self):
        assert self.config.pedigree
        assert os.path.exists(self.config.pedigree), self.config.pedigree

        return PedigreeReader.load_pedigree_file(self.config.pedigree)

    def _load(self, annotator, region, genomes_db):
        loader = RawVariantsLoader(self.config, genomes_db)
        self.ped_df = self._load_pedigree()

        self.vcf = loader.load_vcf(region)

        self.ped_df, self.samples = self._match_pedigree_to_samples(
            self.ped_df, self.vcf.samples)
        self.families_build(self.ped_df, family_class=VcfFamily)
        assert np.all(self.samples == self.ped_df['sample_id'].values)

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
        return sorted([p.sample_index for p in persons])

    def filter_regions(self, v, regions):
        for reg in regions:
            if reg.chr == v.chromosome and \
                    reg.start <= v.position <= reg.stop:
                return True
        return False

    @staticmethod
    def filter_real_attr(va, real_attr_filter):
        result = []
        for key, ranges in real_attr_filter:
            if not va.has_attribute(key):
                return False

            val = va.get_attribute(key)
            if val is None:
                continue
            rmin, rmax = ranges
            if rmin is None:
                result.append(val <= rmax)
            elif rmax is None:
                result.append(val >= rmin)
            else:
                result.append(
                    (val >= rmin) and (val <= rmax)
                )
        if all(result):
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
        if kwargs.get('ultra_rare'):
            if not self.filter_real_attr(
                    allele, [("af_allele_count", (1, 1))]):
                return False

        if kwargs.get('genes') is not None or \
                kwargs.get('effect_types') is not None:
            if not self.filter_gene_effects(
                    allele, kwargs.get('effect_types'), kwargs.get('genes')):
                return False
        if kwargs.get('variant_type') is not None:
            query = kwargs['variant_type']
            if not query.match(
                    [allele.variant_type]):
                return False
        if kwargs.get('person_ids') is not None:
            if allele.is_reference_allele:
                return False
            person_ids = kwargs['person_ids']
            if not set(allele.variant_in_members) & set(person_ids):
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
        return True

    def query_variants(self, **kwargs):
        annot_df = self.annot_df

        if kwargs.get("roles") is not None:
            parsed = kwargs['roles']
            if isinstance(parsed, list):
                parsed = 'any({})'.format(','.join(parsed))
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
                    if allele.allele_index == 0 and not return_reference:
                        continue
                    alleles_matched.append(allele.allele_index)
            if alleles_matched:
                v.set_matched_alleles(alleles_matched)
                yield v

    def wrap_summary_variant(self, records):
        return self.VF.summary_variant_from_records(
            records,
            transmission_type=self.transmission_type)

    def wrap_variants(self, annot_df):
        if annot_df is None:
            return

        variants = self.vcf_vars
        for summary_index, group_df in \
                annot_df.groupby("summary_variant_index"):
            vcf = variants[summary_index]
            summary_variant = self.wrap_summary_variant(
                group_df.to_dict(orient='records'))
            for fam in list(self.families.values()):
                v = self.VF.family_variant_from_vcf(
                    summary_variant, fam, vcf=vcf)
                yield v
        return

    def full_variants_iterator(self):
        sum_df = self.annot_df
        variants = self.vcf_vars
        for summary_index, group_df in \
                sum_df.groupby("summary_variant_index"):
            vcf = variants[summary_index]
            summary_variant = self.wrap_summary_variant(
                group_df.to_dict(orient='records'))

            family_variants = []
            for fam in list(self.families.values()):
                v = self.VF.family_variant_from_vcf(
                    summary_variant, fam, vcf=vcf)
                family_variants.append(v)
            yield summary_variant, family_variants
