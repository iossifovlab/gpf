'''
Created on Dec 13, 2016

@author: lubo
'''
import numpy as np
from pheno.models import MetaVariableManager, MetaVariableModel


class BaseMetaVariables(object):

    def create_tables(self):
        with MetaVariableManager(
                pheno_db=self.pheno_db,
                config=self.config) as vm:
            vm.create_tables()

    def drop_tables(self):
        with MetaVariableManager(
                pheno_db=self.pheno_db,
                config=self.config) as vm:
            vm.drop_tables()

    def _prepare_meta_variables(self):
        meta_variables = []
        for measure_id, measure in self.phdb.measures.items():
            print('processing variable {}'.format(measure_id))

            df = self.phdb._raw_get_measure_values_df(measure)
            v = MetaVariableModel()
            v.variable_id = measure.measure_id
            v.min_value = df[v.variable_id].min()
            v.max_value = df[v.variable_id].max()
            v.has_probands = len(df[df.person_role == 'prb']) > 7
            v.has_siblings = len(df[df.person_role == 'sib']) > 7
            v.has_parents = len(df[
                np.logical_or(
                    df.person_role == 'mom',
                    df.person_role == 'dad'
                )]) > 7
            print(v)
            meta_variables.append(v)

        return meta_variables

    def _save_meta_variables(self, meta_variables):
        with MetaVariableManager(
                pheno_db=self.pheno_db,
                config=self.config) as vm:
            for v in meta_variables:
                vm.save(v)

    def prepare(self):
        self.drop_tables()
        self.create_tables()
        meta_variables = self._prepare_meta_variables()
        self._save_meta_variables(meta_variables)
