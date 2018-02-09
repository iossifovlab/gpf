'''
Created on Feb 8, 2018

@author: lubo
'''
from DAE import genomesDB
from RegionOperations import Region
import numpy as np
import pandas as pd
from variants.loader import StudyLoader, VariantMatcher


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

    def get_gene_regions(self, *gene_symbols):
        regions = []
        gene_models = self.gene_models
        for gs in gene_symbols:
            for gm in gene_models.gene_models_by_gene_name(gs):
                regions.append(Region(gm.chr, gm.tx[0] - 200, gm.tx[1] + 200))
        return regions

    def query_regions(self, *regions):
        assert self.vars_df is not None

        sub_dfs = []
        for reg in regions:
            df = self.vars_df[
                np.logical_and(
                    reg.chr == self.vars_df.chr,
                    np.logical_and(
                        reg.start <= self.vars_df.position,
                        reg.stop >= self.vars_df.position
                    )
                )]
            if len(df) > 0:
                sub_dfs.append(df)
                print(df.index)
        if len(sub_dfs) == 0:
            return None
        elif len(sub_dfs) == 1:
            return sub_dfs[0]
        else:
            return pd.concat(sub_dfs)

    def query_genes(self, *gene_symbols):
        assert self.vars_df is not None
        regions = self.get_gene_regions(*gene_symbols)
        return self.query_regions(*regions)
