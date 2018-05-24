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
from variants.attributes_query import RoleQuery, SexQuery, InheritanceQuery,\
    VariantTypeQuery, parser
from variants.family import VcfFamily
# from variants.variant import VariantFactorySingle
from variants.variant import VariantFactory


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


class RawFamilyVariants(FamiliesBase):

    def __init__(self, config=None, prefix=None, annotator=None, region=None,
                 variant_factory=VariantFactory):
        super(RawFamilyVariants, self).__init__()
        if prefix is not None:
            config = Configure.from_prefix(prefix)
        self.config = config
        assert self.config is not None
        assert isinstance(self.config, Configure)

        self.VF = variant_factory
        self._load(annotator, region)

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

        assert annotator is not None  # FIXME
        if annotator is None:
            self.annot_df = loader.load_annotation()
        else:
            records = []
            for index, v in enumerate(self.vcf_vars):
                split = len(v.ALT) > 1
                for allele_index, alt in enumerate(v.ALT):
                    records.append(
                        (v.CHROM, v.start + 1,
                         v.REF, alt,
                         index, split, allele_index + 1))
            self.annot_df = pd.DataFrame.from_records(
                data=records,
                columns=[
                    'chrom', 'position', 'reference', 'alternative',
                    'var_index', 'split_from_multi_allelic', 'allele_index'])

            annotator.setup(self)
            self.annot_df = annotator.annotate(self.annot_df, self.vcf_vars)

#  FIXME
#         assert len(self.annot_df) == len(self.vcf_vars)
#         assert np.all(self.annot_df.index.values ==
#                       np.arange(len(self.annot_df)))

    def persons_samples(self, persons):
        return sorted([p.get_attr('sampleIndex') for p in persons])

    def filter_regions(self, v, regions):
        for reg in regions:
            if reg.chr == v.chromosome and \
                    reg.start <= v.position and \
                    reg.stop >= v.position:
                return True
        return False

    @staticmethod
    def filter_real_attr(v, real_attr_filter):
        attr = real_attr_filter[0]
        ranges = real_attr_filter[1:]

        for sa in v.alt_alleles:
            val = sa.get_attribute(attr)
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

    def filter_variant(self, v, **kwargs):
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
        if 'family_ids' in kwargs:
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
        if 'inheritance' in kwargs:
            query = kwargs['inheritance']
            if not query.match([v.inheritance]):
                return False
        if 'variant_type' in kwargs:
            query = kwargs['variant_type']
            if not query.match([ad.variant_type for ad in v.details]):
                return False

        if 'real_attr_filter' in kwargs:
            if not self.filter_real_attr(v, kwargs['real_attr_filter']):
                return False

        if 'filter' in kwargs:
            func = kwargs['filter']
            if not func(v):
                print("F:", v.variant_in_roles)
                return False
            else:
                print("T:", v.variant_in_roles)
        return True

    def query_variants(self, **kwargs):
        annot_df = self.annot_df
        vs = self.wrap_variants(annot_df)

        if 'roles' in kwargs and isinstance(kwargs['roles'], str):
            tree = parser.parse(kwargs['roles'])
            matcher = RoleQuery(parser).transform(tree)
            kwargs['roles'] = matcher

        if 'sexes' in kwargs and isinstance(kwargs['sexes'], str):
            tree = parser.parse(kwargs['sexes'])
            matcher = SexQuery(parser).transform(tree)
            kwargs['sexes'] = matcher

        if 'inheritance' in kwargs and isinstance(kwargs['inheritance'], str):
            tree = parser.parse(kwargs['inheritance'])
            matcher = InheritanceQuery(parser).transform(tree)
            kwargs['inheritance'] = matcher

        if 'variant_type' in kwargs and \
                isinstance(kwargs['variant_type'], str):
            tree = parser.parse(kwargs['variant_type'])
            matcher = VariantTypeQuery(parser).transform(tree)
            kwargs['variant_type'] = matcher

        for v in vs:
            if not self.filter_variant(v, **kwargs):
                continue
            yield v

    def wrap_variants(self, annot_df):
        if annot_df is None:
            raise StopIteration()

        variants = self.vcf_vars
        for var_index, group_df in annot_df.groupby(["var_index"]):
            vcf = variants[var_index]
            summary_variant = self.VF.summary_variant_from_records(
                group_df.to_dict(orient='records'))

            for fam in self.families.values():
                vs = self.VF.family_variant_from_vcf(
                    summary_variant, fam, vcf=vcf)
                for v in vs:
                    yield v


if __name__ == "__main__":
    import os
    from variants.vcf_utils import mat2str
    from variants.annotate_variant_effects import \
        VcfVariantEffectsAnnotator
    from variants.annotate_allele_frequencies import \
        VcfAlleleFrequencyAnnotator
    from variants.annotate_composite import AnnotatorComposite

    prefix = os.path.join(
        os.environ.get(
            "DAE_DATA_DIR",
            "/home/lubo/Work/seq-pipeline/data-raw-dev/"
        ),
        "spark/nspark"
    )

    annotator = AnnotatorComposite(annotators=[
        VcfVariantEffectsAnnotator(),
        VcfAlleleFrequencyAnnotator(),
    ])

    fvars = RawFamilyVariants(prefix=prefix, annotator=annotator)

    vs = fvars.query_variants(
        inheritance='unknown',
    )
    for c, v in enumerate(vs):
        print(c, v, v.family_id, mat2str(v.best_st), mat2str(v.gt),
              v.effect_type, v.effect_gene, v.inheritance,
              v.get_attr('all.nAltAlls'), v.get_attr('all.altFreq'))
