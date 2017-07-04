'''
Created on Dec 13, 2016

@author: lubo
'''
from __future__ import print_function

import math
import numpy as np
from pheno.models import ContinuousValueManager, CategoricalValueManager,\
    OrdinalValueManager, VariableManager, PersonManager, VariableModel,\
    ContinuousValueModel, OrdinalValueModel, CategoricalValueModel


class BaseVariables(object):
    INDIVIDUALS = 'individuals'
    CONTINUOUS = 'continuous'
    ORDINAL = 'ordinal'
    CATEGORICAL = 'categorical'
    UNKNOWN = 'unknown'

    @property
    def min_individuals(self):
        return int(self.config.get(self.INDIVIDUALS, 'min_individuals'))

    @property
    def continuous_min_rank(self):
        return int(self.config.get(self.CONTINUOUS, 'min_rank'))

    @property
    def ordinal_min_rank(self):
        return int(self.config.get(self.ORDINAL, 'min_rank'))

    @property
    def categorical_min_rank(self):
        return int(self.config.get(self.CATEGORICAL, 'min_rank'))

    def check_continuous_rank(self, rank, individuals):
        if rank < self.continuous_min_rank:
            return False
        if individuals < self.min_individuals:
            return False
        return True

    def check_ordinal_rank(self, rank, individuals):
        if rank < self.ordinal_min_rank:
            return False
        if individuals < self.min_individuals:
            return False
        return True

    def check_categorical_rank(self, rank, individuals):
        if rank < self.categorical_min_rank:
            return False
        if individuals < self.min_individuals:
            return False
        return True

    def _create_value_tables(self):
        with ContinuousValueManager(
                dbfile=self.get_dbfile()) as vm:
            vm.drop_tables()
            vm.create_tables()
        with CategoricalValueManager(
                dbfile=self.get_dbfile()) as vm:
            vm.drop_tables()
            vm.create_tables()
        with OrdinalValueManager(
                dbfile=self.get_dbfile()) as vm:
            vm.drop_tables()
            vm.create_tables()

    def _create_variable_table(self):
        with VariableManager(
                dbfile=self.get_dbfile()) as vm:
            vm.drop_tables()
            vm.create_tables()

    def load_persons_df(self):
        with PersonManager(dbfile=self.get_dbfile()) as pm:
            df = pm.load_df()
            columns = [c for c in df.columns]
            index = columns.index('role')
            columns[index] = 'person_role'
            df.columns = columns
            df.set_index('person_id', inplace=True)
            return df

    def _build_variable(self, instrument_name, measure_name, mdf):
        measure_id = '{}.{}'.format(instrument_name, measure_name)
        var = VariableModel()
        var.variable_id = measure_id
        var.table_name = instrument_name
        var.variable_name = measure_name

        self._classify_values(var, mdf)
        # self.report_variable(var)
        self._save_variable(var, mdf)

        return var

    def _save_variable(self, var, mdf):
        if var.stats == self.CONTINUOUS:
            self._save_continuous_variable(var, mdf)
        elif var.stats == self.ORDINAL:
            self._save_ordinal_variable(var, mdf)
        elif var.stats == self.CATEGORICAL:
            self._save_categorical_variable(var, mdf)
        else:
            print("OOOPS!!!! unknown variable: {}".format(var))

    def _save_continuous_variable(self, var, mdf):
        assert var.min_value <= var.max_value
        with VariableManager(
                dbfile=self.get_dbfile()) as vm:
            vm.save(var)

        with ContinuousValueManager(
                dbfile=self.get_dbfile()) as vm:
            for _index, row in mdf.iterrows():
                v = ContinuousValueModel()
                v.family_id = row['family_id']
                v.person_id = row['person_id']
                v.person_role = row['person_role']
                v.variable_id = var.variable_id
                v.value = ContinuousValueModel.value_decode(
                    row[var.variable_name])
                vm.save(v)

    def _save_ordinal_variable(self, var, mdf):
        assert var.min_value <= var.max_value
        with VariableManager(
                dbfile=self.get_dbfile()) as vm:
            vm.save(var)

        with OrdinalValueManager(
                dbfile=self.get_dbfile()) as vm:
            for _index, row in mdf.iterrows():
                v = OrdinalValueModel()
                v.family_id = row['family_id']
                v.person_id = row['person_id']
                v.person_role = row['person_role']
                v.variable_id = var.variable_id
                v.value = OrdinalValueModel.value_decode(
                    row[var.variable_name])
                vm.save(v)

    def _save_categorical_variable(self, var, mdf):
        with VariableManager(
                dbfile=self.get_dbfile()) as vm:
            vm.save(var)

        with CategoricalValueManager(
                dbfile=self.get_dbfile()) as vm:
            for _index, row in mdf.iterrows():
                v = CategoricalValueModel()
                v.family_id = row['family_id']
                v.person_id = row['person_id']
                v.person_role = row['person_role']
                v.variable_id = var.variable_id
                v.value = CategoricalValueModel.value_decode(
                    row[var.variable_name])
                vm.save(v)

    def _save_variable_base(self, value_manager, var, mdf):
        with VariableManager(
                dbfile=self.get_dbfile()) as vm:
            vm.save(var)

        with value_manager(
                dbfile=self.get_dbfile()) as vm:
            for _index, row in mdf.iterrows():
                v = value_manager.MODEL()
                v.family_id = row['family_id']
                v.person_id = row['person_id']
                v.person_role = row['person_role']
                v.variable_id = var.variable_id
                v.value = CategoricalValueModel.value_decode(
                    row[var.variable_name])
                vm.save(v)

    @classmethod
    def check_value_type(cls, values):
        boolean = all([isinstance(v, bool) for v in values])
        if boolean:
            return bool

        try:
            vals = [v.strip() for v in values]
            fvals = [float(v) for v in vals if v != '']
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

    @classmethod
    def check_values_domain(cls, values):
        vtype = cls.check_value_type(values)
        if vtype == bool:
            sdomain = [bool(v) for v in values]
        elif vtype == int:
            sdomain = [int(float(v)) for v in values]
        elif vtype == float:
            sdomain = [float(v) for v in values]
        else:
            sdomain = values
        return vtype, sorted(sdomain)

    @classmethod
    def convert_values(cls, values):
        pass

    @classmethod
    def report_variable(cls, var):
        print("-----------------------------------------------")
        print(var)

        print("domain_rank: {}".format(var.domain_rank))
        print("individuals: {}".format(var.individuals))
        print("value_domain: {}".format(var.value_domain))
        print("-----------------------------------------------")

    def _classify_values(self, var, df):
        values = df[var.variable_name]
        if len(values) == 0:
            return self.UNKNOWN

        unique_values = values.unique()
        rank = len(unique_values)
        individuals = len(df)
        values_type = values.dtypes

        var.individuals = individuals
        var.domain_rank = rank

        if values_type == np.object:
            values_type, unique_values = \
                self.check_values_domain(unique_values)

        if values_type == np.int or values_type == np.float or \
                values_type == int or values_type == float or \
                values_type == bool:
            if self.check_continuous_rank(rank, individuals):
                var.stats = self.CONTINUOUS
                var.min_value = min(unique_values)
                var.max_value = max(unique_values)
                var.value_domain = "[{}, {}]".format(
                    var.min_value, var.max_value)
                return self.CONTINUOUS
            elif self.check_ordinal_rank(rank, individuals):
                var.stats = self.ORDINAL
                var.min_value = min(unique_values)
                var.max_value = max(unique_values)
                unique_values = sorted(unique_values)
                var.value_domain = "{}".format(
                    ', '.join([str(v) for v in unique_values]))
                return self.ORDINAL
            elif self.check_categorical_rank(rank, individuals):
                var.stats = self.CATEGORICAL
                unique_values = sorted(unique_values)
                unique_values = [str(v) for v in unique_values
                                 if not isinstance(v, str)]
                var.value_domain = "{}".format(
                    ', '.join([v for v in unique_values]))
                return self.CATEGORICAL
            else:
                var.stats = self.UNKNOWN
                var.value_domain = str(unique_values)
                return self.UNKNOWN

        elif values_type == str:
            if self.check_categorical_rank(rank, individuals):
                var.stats = self.CATEGORICAL
                unique_values = sorted(unique_values)
                var.value_domain = "{}".format(
                    ', '.join([v for v in unique_values]))
                return self.CATEGORICAL

        var.stats = self.UNKNOWN
        var.value_domain = str(unique_values)
        return self.UNKNOWN
