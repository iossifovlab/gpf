'''
Created on Aug 26, 2016

@author: lubo
'''
from pheno.models import VariableManager, \
    VariableModel, RawValueManager
from pheno.precompute.families import PrepareIndividuals
from pheno.utils.load_raw import V15Loader
from pheno.utils.configuration import PhenoConfig
from numpy import rank
import math


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
        def build_where(where):
            if where is None:
                return "table_name='{}'".format(table_name)
            else:
                return "table_name='{}' and  ({})".format(
                    table_name,
                    self.WHERE_DOMAIN)

        with VariableManager(config=self.config) as vm:
            where = build_where(self.WHERE_DOMAIN)
            df = vm.load_df(where=where)
            return df

    def _build_variable_values(self, vm, dfs, variable):
        variable_name = variable['variable_name']
        variable_id = variable['variable_id']
        print("processing variable: {}".format(variable_name))
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
                vm.save(val)

    def _build_table_values(self, table):
        variables = self._load_variables(table)
        if variables is None:
            return

        dfs = self.load_table(
            table, ['prb', 'sib', 'father', 'mother'],
            dtype=str)
        with self.value_manager(config=self.config) as vm:
            for _index, variable in variables.iterrows():
                self._build_variable_values(vm, dfs, variable)

    def prepare(self):
        tables = self._load_tables()
        with self.value_manager(config=self.config) as vm:
            vm.drop_tables()
            vm.create_tables()

        for table in tables:
            self._build_table_values(table)


# class PrepareFloatValues(PrepareValueBase):
#     WHERE_DOMAIN = "measurement_scale='float'"
#
#     def __init__(self, *args, **kwargs):
#
#         super(PrepareFloatValues, self).__init__(
#             value_manager=FloatValueManager, *args, **kwargs)


class PrepareRawValues(PrepareValueBase):
    WHERE_DOMAIN = None

    def __init__(self, *args, **kwargs):
        super(PrepareRawValues, self).__init__(
            value_manager=RawValueManager, *args, **kwargs)


class PrepareVariableDomainRanks(PhenoConfig):

    def __init__(self, *args, **kwargs):
        super(PrepareVariableDomainRanks, self).__init__(*args, **kwargs)

    def _rank(self, var):
        where = "variable_id='{}'".format(var.variable_id)
        with RawValueManager(config=self.config) as vm:
            df = vm.load_df(where=where)
            if(df is None):
                return 0, 0
            individuals = len(df)
            rank = len(df.value.unique())

            return rank, individuals

    def prepare(self):
        with VariableManager(config=self.config) as vm:
            variables = vm.load_df()

        for _index, row in variables.iterrows():
            var = VariableModel.create_from_df(row)
            print("calculating rank of {}".format(var.variable_id))
            rank, individuals = self._rank(var)

            var.domain_rank = rank
            var.individuals = individuals
            with VariableManager(config=self.config) as vm:
                vm.save(var)


class PrepareValueClassification(PhenoConfig):
    INDIVIDUALS_CUTOFF = 77
    RANK_CUTOFF = 1

    def __init__(self, *args, **kwargs):
        super(PrepareValueClassification, self).__init__(*args, **kwargs)

    def check_type(self, values):
        try:
            fvals = [float(v) for v in values]
        except ValueError:
            fvals = None
        if fvals is None:
            return str

        hvals = [math.floor(v) for v in fvals]
        lvals = [math.ceil(v) for v in fvals]

        check_float = [v1 == v2 for (v1, v2) in zip(hvals, lvals)]
        if all(check_float):
            return int
        else:
            return float

    def check_domain_choice(self, domain_choice_label):
        def strip_brackets(s):
            if s[0] == '[':
                s = s[1:]
            if s[-1] == ']':
                s = s[:-1]
            return s

        def is_int_list(s):
            s = strip_brackets(s)
            l = s.split(',')
            assert isinstance(l, list)
            l = [v.strip() for v in l]
            l = [v for v in l if v != 'null']

            if self.check_type(l) == int:
                return l
            return None

        def is_str_list(s):
            s = strip_brackets(s)
            l = s.split(',')
            assert isinstance(l, list)
            l = [v.strip() for v in l]
            l = [v for v in l if v != 'null']
            if self.check_type(l) == str:
                return l
            return None

        dtype = 'nominal'

        if domain_choice_label is None or \
                len(domain_choice_label) == 0 or \
                domain_choice_label == '[]':
            dtype = 'continuous', float

        elif is_int_list(domain_choice_label):
            dtype = 'ordinal', is_int_list(domain_choice_label)

        elif is_str_list(domain_choice_label):
            dtype = 'nominal', is_str_list(domain_choice_label)

        return dtype

    def check_domain_type(self, variable, values):
        if variable.domain_choice_label is None:
            dtype = 'continuous'
        elif variable.domain_choice_label == '[]':
            dtype = 'continuous'

        return dtype

    def classify_variable(self, var):
        with RawValueManager(config=self.config) as vm:
            df = vm.load_values(var)
            unique = df.value.unique()
            value_type = self.check_type(unique)

            return value_type

        return None
