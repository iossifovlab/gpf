'''
Created on Aug 26, 2016

@author: lubo
'''
import numpy as np

from pheno.models import VariableManager, FloatValueModel, FloatValueManager
from pheno.precompute.families import PrepareIndividuals
from pheno.utils.load_raw import V15Loader


class PrepareFloatValues(V15Loader):

    def __init__(self, *args, **kwargs):
        super(PrepareFloatValues, self).__init__(*args, **kwargs)

    def _load_tables(self):
        with VariableManager(config=self.config) as vm:
            df = vm.load_df(
                where="measurement_scale='float' or "
                "measurement_scale='integer'")

            tables = df.table_name.unique()
            return tables

    def _load_variables(self, table_name):
        with VariableManager(config=self.config) as vm:
            where = "table_name='{}' and " \
                "(measurement_scale='float' or " \
                "measurement_scale='integer')".format(table_name)
            df = vm.load_df(where=where)
            return df

    def _build_variable_values(self, dfs, variable):
        variable_name = variable['variable_name']
        variable_id = variable['variable_id']
        print("processing variable: {}".format(variable_name))
        with FloatValueManager(config=self.config) as fvm:
            for df in dfs:
                if variable_name not in df.columns:
                    continue
                for _vindex, vrow in df.iterrows():
                    val = FloatValueModel()
                    val.value = vrow[variable_name]
                    if np.isnan(val.value):
                        continue
                    val.id = None
                    val.variable_id = variable_id
                    val.person_id = vrow['individual']
                    [val.family_id, role] = val.person_id.split('.')
                    val.person_role = PrepareIndividuals._role_type(
                        role)
                    fvm.save(val)

    def _build_table_values(self, table):
        variables = self._load_variables(table)
        if variables is None:
            return

        dfs = self.load_table(
            table, ['prb', 'sib', 'father', 'mother'])
        for _index, variable in variables.iterrows():
            self._build_variable_values(dfs, variable)

    def prepare(self):
        tables = self._load_tables()
        with FloatValueManager(config=self.config) as fvm:
            fvm.drop_tables()
            fvm.create_tables()

        for table in tables:
            self._build_table_values(table)
