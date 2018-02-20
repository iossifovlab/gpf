'''
Created on Feb 8, 2018

@author: lubo
'''
from __future__ import print_function

from DAE import genomesDB
from RegionOperations import Region
import numpy as np
import pandas as pd
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


class RawFamilyVariants(Families):

    def __init__(self, config=None, prefix=None):
        super(RawFamilyVariants, self).__init__()
        if prefix is not None:
            config = Configure.from_prefix(prefix)
        self.config = config
        assert self.config is not None
        assert isinstance(self.config, Configure)

        self._gene_models = None
        self._load()

    def _load(self):
        loader = RawVariantsLoader(self.config)
        self.ped_df = loader.load_pedigree()
        self.families_build(self.ped_df)

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
        return v.in_persons(person_ids)

    def filter_families(self, v, family_ids):
        return v.family_id in family_ids

    def filter_roles(self, v, roles):
        role_query = RoleQuery.from_list(roles)
        mems = v.members_with_role(role_query)
        return v.in_persons(mems)

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
        return True

    def query_variants(self, **kwargs):
        df = self.vars_df
        vs = self.wrap_variants(df)

        for v in vs:
            if not self.filter_variant(v, **kwargs):
                continue
            yield v

    @property
    def gene_models(self):
        if not self._gene_models:
            self._gene_models = genomesDB.get_gene_models()  # @UndefinedVariable @IgnorePep8
        return self._gene_models

    def get_gene_regions(self, gene_symbols):
        regions = []
        gene_models = self.gene_models
        for gs in gene_symbols:
            for gm in gene_models.gene_models_by_gene_name(gs):
                regions.append(Region(gm.chr, gm.tx[0] - 200, gm.tx[1] + 200))
        return regions

    def query_regions(self, regions, df=None):
        assert type(regions) == list

        if df is None:
            df = self.vars_df

        sub_dfs = []
        for reg in regions:
            rdf = df[
                np.logical_and(
                    reg.chr == self.vars_df.chr,
                    np.logical_and(
                        reg.start <= self.vars_df.position,
                        reg.stop >= self.vars_df.position
                    )
                )]
            if len(rdf) > 0:
                sub_dfs.append(rdf)
        if len(sub_dfs) == 0:
            return None
        elif len(sub_dfs) == 1:
            return sub_dfs[0]
        else:
            return pd.concat(sub_dfs)

    def query_genes(self, gene_symbols, df):
        if df is None:
            return None
        regions = self.get_gene_regions(gene_symbols)
        df = self.query_regions(regions, df)
        index = df['effectGene'].apply(
            lambda effect_gene:
            len(filter_gene_effects(effect_gene, None, gene_symbols)) > 0
        )
        return df[index]

    def query_effect_types(self, effect_types, df):
        if df is None:
            return None

        index = df['effectGene'].apply(
            lambda effect_gene:
            len(filter_gene_effects(effect_gene, effect_types, None)) > 0
        )
        return df[index]

    def query_genes_effect_types(self, effect_types, gene_symbols,  df):
        if df is None:
            return None

        regions = self.get_gene_regions(gene_symbols)
        df = self.query_regions(regions, df)
        index = df['effectGene'].apply(
            lambda effect_gene:
            len(filter_gene_effects(
                effect_gene, effect_types, gene_symbols)) > 0
        )
        return df[index]

    def query_persons(self, person_ids, df):
        if df is None:
            raise StopIteration()

        samples = self.ped_df[
            self.ped_df['personId'].isin(set(person_ids))
        ].index.values

        alleles = Family.samples_to_alleles(samples)

        matched = pd.Series(
            data=np.zeros(len(self.vars_df), dtype=np.bool),
            index=self.vars_df.index, dtype=np.bool)

        families = self.families_query_by_person(person_ids)

        variants = self.vcf_vars

        for index, row in df.iterrows():
            vcf = variants[index]
            gt = vcf.gt_idxs[alleles]
            if np.all(gt == 0):
                continue

            matched[index] = True
            summary_variant = FamilyVariant.from_dict(row)

            for fam in families.values():
                gt = vcf.gt_idxs[fam.palleles(person_ids)]
                if np.all(gt == 0):
                    continue
                v = summary_variant.clone(). \
                    set_family(fam). \
                    set_genotype(vcf)
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

    def query_families(self, family_ids, df=None):
        samples = self.ped_df['familyId'].isin(set(family_ids)).values
        persons = (self.ped_df['personId'].values)[samples]
        return self.query_persons(persons, df)

    def query_roles(self, role_queries, df=None):
        assert role_queries

        for role_query in role_queries:
            samples = self.ped_df[
                (self.ped_df['role'] & role_query.value).values.astype(np.bool)
            ].personId.values
            for v in self.query_persons(samples, df):
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
