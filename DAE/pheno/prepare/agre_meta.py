'''
Created on Dec 8, 2016

@author: lubo
'''
import numpy as np

from pheno.prepare.agre_families import AgreLoader
from pheno.pheno_factory import PhenoFactory
from pheno.models import MetaVariableManager, \
    MetaVariableModel


class PrepareMetaVariables(AgreLoader):

    def __init__(self):
        super(PrepareMetaVariables, self).__init__()
        self.pheno_factory = PhenoFactory()
        assert self.pheno_factory.has_pheno_db('agre')
        self.phdb = self.pheno_factory.get_pheno_db('agre')

    def create_tables(self):
        with MetaVariableManager(pheno_db='agre') as vm:
            vm.create_tables()

    def drop_tables(self):
        with MetaVariableManager(pheno_db='agre') as vm:
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
        with MetaVariableManager(pheno_db='agre') as vm:
            for v in meta_variables:
                vm.save(v)

    def prepare(self):
        self.drop_tables()
        self.create_tables()
        meta_variables = self._prepare_meta_variables()
        self._save_meta_variables(meta_variables)
