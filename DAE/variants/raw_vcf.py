'''
Created on Feb 8, 2018

@author: lubo
'''
from __future__ import print_function

from RegionOperations import Region
import numpy as np
from variants.loader import RawVariantsLoader
from numba import jit
from variants.family import Families, Family
from variants.variant import FamilyVariant
from variants.configure import Configure
from variants.roles import RoleQuery


@jit
def split_gene_effect(effects):
    result = []
    if not isinstance(effects, str):
        return result
    for ge in effects.split("|"):
        sym, eff = ge.split(":")
        result.append({'sym': sym, 'eff': eff})
    return result


@jit
def parse_gene_effect(effect):
    if effect in set(["CNV+", "CNV-", "intergenic"]):
        return [{'eff': effect, 'sym': ""}]

    return split_gene_effect(effect)


@jit
def filter_gene_effects(effects, effect_types, gene_symbols):
    gene_effects = parse_gene_effect(effects)
    if effect_types is None:
        return [ge for ge in gene_effects if ge['sym'] in gene_symbols]
    if gene_symbols is None:
        return [ge for ge in gene_effects if ge['eff'] in effect_types]
    return [ge for ge in gene_effects
            if ge['eff'] in effect_types and ge['sym'] in gene_symbols]


class VcfFamily(Family):

    @staticmethod
    def samples_to_alleles_index(samples):
        return np.stack([2 * samples, 2 * samples + 1]). \
            reshape([1, 2 * len(samples)], order='F')[0]

    def __init__(self, family_id, ped_df):
        super(VcfFamily, self).__init__(family_id, ped_df)

        self.samples = self.ped_df.index.values
        self.alleles = VcfFamily.samples_to_alleles_index(self.samples)

    def vcf_samples_index(self, person_ids):
        return self.ped_df[
            self.ped_df['personId'].isin(set(person_ids))
        ].index.values

    def vcf_alleles_index(self, person_ids):
        p = self.vcf_samples_index(person_ids)
        return VcfFamily.samples_to_alleles_index(p)


class RawFamilyVariants(Families):

    def __init__(self, config=None, prefix=None):
        super(RawFamilyVariants, self).__init__()
        if prefix is not None:
            config = Configure.from_prefix(prefix)
        self.config = config
        assert self.config is not None
        assert isinstance(self.config, Configure)

        self._load()

    def _load(self):
        loader = RawVariantsLoader(self.config)
        self.ped_df = loader.load_pedigree()
        self.families_build(self.ped_df, family_class=VcfFamily)

        self.vcf = loader.load_vcf()
        self.samples = self.vcf.samples

        assert np.all(self.samples == self.ped_df['personId'].values)

        self.vars_df = loader.load_annotation()
        self.vcf_vars = list(self.vcf.vcf)
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

    def filter_gene_effects(self, v, effect_types, genes):
        return filter_gene_effects(v.effect_gene, effect_types, genes)

    def filter_persons(self, v, person_ids):
        return bool(v.variant_in_members & set(person_ids))

    def filter_families(self, v, family_ids):
        return v.family_id in family_ids

    def filter_roles(self, v, roles):
        role_query = RoleQuery.from_list(roles)
        roles = RoleQuery.from_list(v.variant_in_roles)
        return role_query.match(roles)

    def filter_variant(self, v, **kwargs):
        if 'regions' in kwargs:
            if not self.filter_regions(v, kwargs['regions']):
                return False
        if 'genes' in kwargs or 'effect_types' in kwargs:
            if not self.filter_gene_effects(
                    v, kwargs.get('effect_types'), kwargs.get('genes')):
                return False
        if 'person_ids' in kwargs:
            if not self.filter_persons(v, kwargs.get('person_ids')):
                return False
        if 'family_ids' in kwargs:
            if not self.filter_families(v, kwargs.get('family_ids')):
                return False
        if 'roles' in kwargs:
            if not self.filter_roles(v, kwargs.get('roles')):
                return False
        if 'filter' in kwargs:
            fun = kwargs['filter']
            if not fun(v):
                return False
        return True

    def query_variants(self, **kwargs):
        df = self.vars_df
        vs = self.wrap_variants(df)

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

    prefix = os.environ.get(
        "DAE_UAGRE_PREFIX=",
        "/home/lubo/Work/seq-pipeline/data-raw-dev/uagre/test_agre"
    )

    fvars = RawFamilyVariants(prefix=prefix)

    vs = fvars.query_variants(regions=[Region("1", 130000, 139999)])
    for v in vs:
        print(v, v.effect_type, v.effect_gene, v.is_medelian(), sep="\t")
        print(v.gt)
        print(v.best_st)
