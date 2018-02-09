'''
Created on Feb 8, 2018

@author: lubo
'''
from DAE import genomesDB
from RegionOperations import Region
import numpy as np
import pandas as pd
from variants.loader import StudyLoader, VariantMatcher
from numba import jit


@jit
def split_gene_effect(effects):
    result = []
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


class Study(object):

    def __init__(self, config):
        self.config = config
        self._gene_models = None

    def load(self):
        loader = StudyLoader(self.config)
        self.ped_df, self.ped = loader.load_pedigree()
        self.vcf = loader.load_vcf()
        self.samples = self.vcf.samples

        assert np.all(self.samples == self.ped_df['personId'].values)
        matcher = VariantMatcher(self.config)
        matcher.match()
        self.vars_df = matcher.vars_df
        self.vcf_vars = matcher.vcf_vars
        assert len(self.vars_df) == len(self.vcf_vars)

    def query_variants(self, **kwargs):
        pass

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

    def query_genes(self, gene_symbols, df=None):
        regions = self.get_gene_regions(gene_symbols)
        df = self.query_regions(regions, df)
        index = df['effectGene'].apply(
            lambda effect_gene:
            len(filter_gene_effect(effect_gene, None, gene_symbols)) > 0
        )
        return df[index]

    def query_effect_types(self, effect_types, df=None):
        if df is None:
            df = self.vars_df
        index = df['effectGene'].apply(
            lambda effect_gene:
            len(filter_gene_effect(effect_gene, effect_types, None)) > 0
        )
        return df[index]

    def query_genes_effect_types(self, effect_types, gene_symbols,  df=None):
        regions = self.get_gene_regions(gene_symbols)
        df = self.query_regions(regions, df)
        index = df['effectGene'].apply(
            lambda effect_gene:
            len(filter_gene_effect(
                effect_gene, effect_types, gene_symbols)) > 0
        )
        return df[index]
