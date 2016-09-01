'''
Created on Aug 26, 2016

@author: lubo
'''
from pheno.models import VariableManager, FloatValueManager,\
    TextValueManager
from pheno.precompute.families import PrepareIndividuals
from pheno.utils.load_raw import V15Loader


class PrepareValueBase(V15Loader):

    def __init__(self, value_manager, *args, **kwargs):
        super(PrepareValueBase, self).__init__(*args, **kwargs)
        self.value_manager = value_manager

    def _load_tables(self):
        with VariableManager(config=self.config) as vm:
            df = vm.load_df(where=self.WHERE_DOMAIN)

            tables = df.table_name.unique()
            return tables

    def _load_variables(self, table_name):
        with VariableManager(config=self.config) as vm:
            where = "table_name='{}' and  ({})".format(
                table_name,
                self.WHERE_DOMAIN)
            df = vm.load_df(where=where)
            return df

    def _build_variable_values(self, dfs, variable):
        variable_name = variable['variable_name']
        variable_id = variable['variable_id']
        print("processing variable: {}".format(variable_name))
        with self.value_manager(config=self.config) as fvm:
            for df in dfs:
                if variable_name not in df.columns:
                    continue
                for _vindex, vrow in df.iterrows():
                    value_model = self.value_manager.MODEL
                    val = value_model()
                    val.value = vrow[variable_name]
                    if value_model.isnull(val.value):
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
        with self.value_manager(config=self.config) as vm:
            vm.drop_tables()
            vm.create_tables()

        for table in tables:
            self._build_table_values(table)


class PrepareFloatValues(PrepareValueBase):
    WHERE_DOMAIN = "measurement_scale='float'"

    def __init__(self, *args, **kwargs):

        super(PrepareFloatValues, self).__init__(
            value_manager=FloatValueManager, *args, **kwargs)


class PrepareTextValues(PrepareValueBase):
    WHERE_DOMAIN = "measurement_scale != 'float'"

    def __init__(self, *args, **kwargs):
        super(PrepareTextValues, self).__init__(
            value_manager=TextValueManager, *args, **kwargs)
