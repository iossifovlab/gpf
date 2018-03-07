'''
Created on Feb 8, 2018

@author: lubo
'''
from __future__ import print_function

import numpy as np
import pandas as pd

from variants.loader import RawVariantsLoader
from variants.family import FamiliesBase
from variants.variant import FamilyVariant
from variants.configure import Configure
from variants.attributes import RoleQuery, SexQuery, InheritanceQuery
from RegionOperations import Region
from variants.vcf_utils import VcfFamily
import sys


def split_gene_effect(effects):
    result = []
    if not isinstance(effects, str):
        return result
    for ge in effects.split("|"):
        sym, eff = ge.split(":")
        result.append({'sym': sym, 'eff': eff})
    return result


def parse_gene_effect(effect):
    if effect in set(["CNV+", "CNV-", "intergenic"]):
        return [{'eff': effect, 'sym': ""}]

    return split_gene_effect(effect)


class RawFamilyVariants(FamiliesBase):

    def __init__(self, config=None, prefix=None, annotate=False):
        super(RawFamilyVariants, self).__init__()
        if prefix is not None:
            config = Configure.from_prefix(prefix)
        self.config = config
        assert self.config is not None
        assert isinstance(self.config, Configure)

        self._load(annotate)

    def _match_pedigree_to_samples(self, ped_df, samples):
        samples_needed = set(samples)
        pedigree_samples = set(ped_df['sampleId'].values)
        missing_samples = samples_needed.difference(pedigree_samples)
        print("pedigree missing samples: ", missing_samples, file=sys.stderr)

        samples_needed = samples_needed.difference(missing_samples)
        assert samples_needed.issubset(pedigree_samples)

        pedigree = []
        for record in ped_df.to_dict(orient='record'):
            if record['sampleId'] in samples_needed:
                pedigree.append(record)
        assert len(pedigree) == len(samples_needed)
        samples_list = [s for s in samples if s in samples_needed]

        pedigree = sorted(
            pedigree, key=lambda p: samples_list.index(p['sampleId']))

        ped_df = pd.DataFrame(pedigree)
        return ped_df, np.array(samples_list)

    def _load(self, annotate):
        loader = RawVariantsLoader(self.config)
        self.ped_df = loader.load_pedigree()

        self.vcf = loader.load_vcf()

        self.ped_df, self.samples = self._match_pedigree_to_samples(
            self.ped_df, self.vcf.samples)
        self.families_build(self.ped_df, family_class=VcfFamily)
        assert np.all(self.samples == self.ped_df['sampleId'].values)

        self.vcf_vars = self.vcf.vars

        if not annotate:
            self.vars_df = loader.load_annotation()
        else:
            pass

        assert len(self.vars_df) == len(self.vcf_vars)
        assert np.all(self.vars_df.index.values ==
                      np.arange(len(self.vars_df)))

    def filter_regions(self, v, regions):
        for reg in regions:
            if reg.chr == v.chromosome and \
                    reg.start <= v.position and \
                    reg.stop >= v.position:
                return True
        return False

    @staticmethod
    def filter_gene_effects(v, effect_types, genes):
        gene_effects = parse_gene_effect(v.effect_gene[0])
        if effect_types is None:
            return [ge for ge in gene_effects if ge['sym'] in genes]
        if genes is None:
            return [ge for ge in gene_effects if ge['eff'] in effect_types]
        return [ge for ge in gene_effects
                if ge['eff'] in effect_types and ge['sym'] in genes]

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

        if 'filter' in kwargs:
            func = kwargs['filter']
            if not func(v):
                print("F:", v.variant_in_roles)
                return False
            else:
                print("T:", v.variant_in_roles)
        return True

    def query_variants(self, **kwargs):
        df = self.vars_df
        vs = self.wrap_variants(df)

        if 'roles' in kwargs and isinstance(kwargs['roles'], str):
            query = RoleQuery.parse(kwargs['roles'])
            kwargs['roles'] = query

        if 'sexes' in kwargs and isinstance(kwargs['sexes'], str):
            query = SexQuery.parse(kwargs['sexes'])
            kwargs['sexes'] = query

        if 'inheritance' in kwargs and isinstance(kwargs['inheritance'], str):
            query = InheritanceQuery.parse(kwargs['inheritance'])
            kwargs['inheritance'] = query

        for v in vs:
            if not self.filter_variant(v, **kwargs):
                continue
            yield v

    def wrap_variants(self, df):
        if df is None:
            raise StopIteration()

        variants = self.vcf_vars
        for index, row in df.iterrows():
            vcf = variants[index]

            summary_variant = FamilyVariant.from_dict(row)

            for fam in self.families.values():
                v = summary_variant.clone(). \
                    set_family(fam). \
                    set_genotype(vcf)
                yield v


if __name__ == "__main__":
    import os
    from variants.vcf_utils import mat2str

    prefix = os.environ.get(
        "DAE_UAGRE_PREFIX",
        "/home/lubo/Work/seq-pipeline/data-raw-dev/nagre/nano_agre1"
    )

    fvars = RawFamilyVariants(prefix=prefix)

    vs = fvars.query_variants(
        inheritance='denovo or omission',
    )
    for c, v in enumerate(vs):
        print(c, v, mat2str(v.best_st),
              v.effect_type, v.effect_gene, v.inheritance)

    regions = [Region("1", 900718, 900719)]
    vs = fvars.query_variants(regions=regions)

    for v in vs:
        print(v, mat2str(v.best_st))
