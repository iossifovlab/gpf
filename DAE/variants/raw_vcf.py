'''
Created on Feb 8, 2018

@author: lubo
'''
from __future__ import print_function

from DAE import genomesDB
from RegionOperations import Region
import numpy as np
import pandas as pd
from variants.loader import RawVariantsLoader, VariantMatcher
from numba import jit
from variants.family import Families, Family
from variants.variant import FamilyVariant


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
def filter_gene_effect(effects, effect_types, gene_symbols):
    gene_effects = parse_gene_effect(effects)
    if effect_types is None:
        return [ge for ge in gene_effects if ge['sym'] in gene_symbols]
    if gene_symbols is None:
        return [ge for ge in gene_effects if ge['eff'] in effect_types]
    return [ge for ge in gene_effects
            if ge['eff'] in effect_types and ge['sym'] in gene_symbols]


class RawFamilyVariants(Families):

    def __init__(self, config):
        super(RawFamilyVariants, self).__init__()
        self.config = config
        self._gene_models = None

    def load(self):
        loader = RawVariantsLoader(self.config)
        self.ped_df = loader.load_pedigree()
        self.families_build(self.ped_df)

        self.vcf = loader.load_vcf()
        self.samples = self.vcf.samples

        assert np.all(self.samples == self.ped_df['personId'].values)
        # matcher = VariantMatcher(self.config)
        # matcher.match()
        # self.vars_df = matcher.vars_df
        # self.vcf_vars = matcher.vcf_vars
        self.vars_df = loader.load_summary()
        self.vcf_vars = list(self.vcf.vcf)
        assert len(self.vars_df) == len(self.vcf_vars)
        assert np.all(self.vars_df.index.values ==
                      np.arange(len(self.vars_df)))

    def query_variants(self, **kwargs):
        df = self.vars_df

        if 'regions' in kwargs:
            df = self.query_regions(kwargs['regions'], df)
        if 'genes' in kwargs:
            df = self.query_genes(kwargs['genes'], df)
        if 'effect_types' in kwargs:
            df = self.query_effect_types(kwargs['effect_types'], df)

        if df is None:
            raise StopIteration()

        if 'roles' in kwargs:
            vs = self.query_roles(kwargs['roles'], df)
        elif 'family_ids' in kwargs:
            vs = self.query_families(kwargs['family_ids'], df)
        elif 'person_ids' in kwargs:
            vs = self.query_persons(kwargs['person_ids'], df)
        else:
            vs = self.wrap_variants(df)
        for v in vs:
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
            len(filter_gene_effect(effect_gene, None, gene_symbols)) > 0
        )
        return df[index]

    def query_effect_types(self, effect_types, df):
        if df is None:
            return None

        index = df['effectGene'].apply(
            lambda effect_gene:
            len(filter_gene_effect(effect_gene, effect_types, None)) > 0
        )
        return df[index]

    def query_genes_effect_types(self, effect_types, gene_symbols,  df):
        if df is None:
            return None

        regions = self.get_gene_regions(gene_symbols)
        df = self.query_regions(regions, df)
        index = df['effectGene'].apply(
            lambda effect_gene:
            len(filter_gene_effect(
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
    from variants.configure import Configure

    work_dir = os.environ.get(
        "DAE_DATA_DIR",
        "/home/lubo/Work/seq-pipeline/data-variants/"
    )

    config = Configure.from_file(work_dir)
    print(config)

    fvars = RawFamilyVariants(config)
    fvars.load()

    vs = fvars.query_variants(regions=[Region("1", 130000, 139999)])
    for v in vs:
        print(v, v.effect_type, v.effect_gene, v.is_medelian(), sep="\t")
        print(v.gt)
        print(v.best_st)
