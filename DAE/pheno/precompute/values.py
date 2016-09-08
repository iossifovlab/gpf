'''
Created on Aug 26, 2016

@author: lubo
'''
from pheno.models import VariableManager, \
    VariableModel, RawValueManager, ContinuousValueManager,\
    CategoricalValueManager, OrdinalValueManager, ContinuousValueModel,\
    OrdinalValueModel, CategoricalValueModel
from pheno.precompute.families import PrepareIndividuals
from pheno.utils.load_raw import V15Loader
from pheno.utils.configuration import PhenoConfig

import math
import pandas as pd


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
    CONTINUOUS = 'continuous'
    RANGE = 'range'
    ORDINAL = 'ordinal'
    CATEGORICAL = 'categorical'
    UNKNOWN = 'unknown'

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

    def check_domain_choice_label(self, domain_choice_label):
        def strip_brackets(s):
            if s is None or len(s) == 0:
                return s
            if s[0] == '[':
                s = s[1:]
            if s[-1] == ']':
                s = s[:-1]
            return s.strip()

        def is_int_list(s):
            l = s.split(',')
            assert isinstance(l, list)
            l = [v.strip() for v in l]
            l = [v for v in l if v != 'null']

            if self.check_type(l) == int:
                return [int(v) for v in l]
            return None

        def is_str_list(s):
            l = s.split(',')
            assert isinstance(l, list)
            if len(l) <= 1:
                return None
            l = [v.strip() for v in l]
            l = [v for v in l if v != 'null']
            if self.check_type(l) == str:
                return l
            return None

        def is_int_range(s):
            if '-' in s:
                l = s.split('-')
            elif 'to' in s:
                l = s.split('to')
            else:
                return None

            if len(l) != 2:
                return None
            l = [v.strip() for v in l]

            if self.check_type(l) == int:
                return [int(float(v)) for v in l]
            return None

        dtype = 'unknown', None

        label = strip_brackets(domain_choice_label)
        if label is None or \
                len(label) == 0:
            dtype = self.CONTINUOUS, float

        elif is_int_list(label):
            dtype = self.ORDINAL, sorted(is_int_list(label))

        elif is_str_list(label):
            dtype = self.CATEGORICAL, sorted(is_str_list(label))
        elif is_int_range(label):
            return self.RANGE, is_int_range(label)

        return dtype

    def check_value_domain(self, values):
        vtype = self.check_type(values)
        if vtype == int:
            sdomain = [int(float(v)) for v in values]
        elif vtype == float:
            sdomain = [float(v) for v in values]
        else:
            sdomain = values
        return vtype, sorted(sdomain)

    def check_continuous(self, variable, values):
        dtype, ddomain = self.check_domain_choice_label(
            variable.domain_choice_label)
        rank = len(values.unique())
        individuals = len(values)

        if not (dtype == self.CONTINUOUS or dtype == self.RANGE):
            return False

        if not (ddomain == float or ddomain == int or
                isinstance(ddomain, list)):
            return False

        if not (variable.domain == 'meta.integer_t' or
                variable.domain == 'meta.float_t'):
            return False

        if rank < int(self[self.CONTINUOUS, 'min_rank']):
            return False

        if individuals < int(self[self.CONTINUOUS, 'min_individuals']):
            return False

        return True

    def check_ordinal(self, variable, values):
        dtype, _ddomain = self.check_domain_choice_label(
            variable.domain_choice_label)
        vtype, _vdomain = self.check_value_domain(values)

        rank = len(values.unique())
        individuals = len(values)

        if variable.domain in ['meta.text_t', 'meta.memo_t', 'meta.file_t']:
            return False

        if vtype != int:
            return False

        if not (dtype == self.ORDINAL or dtype == self.CONTINUOUS):
            return False

        if rank < int(self[self.ORDINAL, 'min_rank']) or \
                rank > int(self[self.ORDINAL, 'max_rank']):
            return False

        if individuals < int(self[self.ORDINAL, 'min_individuals']):
            return False

        return True

    def check_categorical(self, variable, values):
        rank = len(values.unique())
        individuals = len(values)

        if rank < int(self[self.ORDINAL, 'min_rank']) or \
                rank > int(self[self.ORDINAL, 'max_rank']):
            return False

        if individuals < int(self[self.ORDINAL, 'min_individuals']):
            return False

        return True

    def classify_variable(self, variable_id):
        with VariableManager(config=self.config) as vm:
            df = vm.load_df(where="variable_id = '{}'".format(variable_id))
            assert len(df) <= 1
            if len(df) == 0:
                return self.UNKNOWN
            variable = VariableModel.create_from_df(df.loc[0])

        with RawValueManager(config=self.config) as vm:
            df = vm.load_values(variable)
            if len(df) == 0:
                return self.UNKNOWN
            if self.check_continuous(variable, df.value):
                return self.CONTINUOUS
            elif self.check_ordinal(variable, df.value):
                return self.ORDINAL
            elif self.check_categorical(variable, df.value):
                return self.CATEGORICAL

        return self.UNKNOWN

    def _create_value_tables(self):
        with ContinuousValueManager(config=self.config) as vm:
            vm.drop_tables()
            vm.create_tables()
        with CategoricalValueManager(config=self.config) as vm:
            vm.drop_tables()
            vm.create_tables()
        with OrdinalValueManager(config=self.config) as vm:
            vm.drop_tables()
            vm.create_tables()

    def _prepare_continuous_variable(self, variable, df):
        print(
            "processing continuous variable: {}".format(variable.variable_id))

        variable.stats = self.CONTINUOUS
        variable.rank = len(df.value.unique())
        variable.individuals = len(df.value)

        vals = pd.Series(df.index)

        with ContinuousValueManager(config=self.config) as valm:
            for vindex, row in df.iterrows():
                value = ContinuousValueModel.create_from_df(row)
                valm.save(value)
                vals[vindex] = value.value

        variable.min_value = vals.min()
        variable.max_value = vals.max()

        assert variable.min_value <= variable.max_value
        with VariableManager(config=self.config) as vm:
            vm.save(variable)

    def _prepare_ordinal_variable(self, variable, df):
        print(
            "processing ordinal variable: {}".format(variable.variable_id))
        variable.stats = self.ORDINAL
        variable.rank = len(df.value.unique())
        variable.individuals = len(df.value)

        vals = pd.Series(df.index)

        with OrdinalValueManager(config=self.config) as valm:
            for vindex, row in df.iterrows():
                value = OrdinalValueModel.create_from_df(row)
                valm.save(value)
                vals[vindex] = value.value

        variable.min_value = vals.min()
        variable.max_value = vals.max()

        assert variable.min_value <= variable.max_value
        with VariableManager(config=self.config) as vm:
            vm.save(variable)

    def _prepare_categorical_variable(self, variable, df):
        print(
            "processing categorical variable: {}".format(variable.variable_id))
        variable.stats = self.CATEGORICAL
        variable.rank = len(df.value.unique())
        variable.individuals = len(df.value)
        with VariableManager(config=self.config) as vm:
            vm.save(variable)
        with CategoricalValueManager(config=self.config) as valm:
            for _vindex, value in df.iterrows():
                value = CategoricalValueModel.create_from_df(value)
                valm.save(value)

    def prepare(self):
        self._create_value_tables()

        with VariableManager(config=self.config) as variable_manager:
            variables = variable_manager.load_df()

        for _index, variable in variables.iterrows():
            with RawValueManager(config=self.config) as vm:
                df = vm.load_df(
                    where="variable_id = '{}'"
                    .format(variable.variable_id))
            if len(df) == 0:
                with VariableManager(config=self.config) as variable_manager:
                    variable.rank = 0
                    variable.individuals = 0
                    variable.stats = 'empty'
                    variable_manager.save(variable)

            elif self.check_continuous(variable, df.value):
                self._prepare_continuous_variable(variable, df)
            elif self.check_ordinal(variable, df.value):
                self._prepare_ordinal_variable(variable, df)
            elif self.check_categorical(variable, df.value):
                self._prepare_categorical_variable(variable, df)
