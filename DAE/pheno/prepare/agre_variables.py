'''
Created on Dec 7, 2016

@author: lubo
'''
import itertools
import math

import numpy as np
from pheno.models import VariableModel, ContinuousValueManager,\
    ContinuousValueModel, VariableManager, CategoricalValueManager,\
    OrdinalValueManager, PersonManager, OrdinalValueModel, \
    CategoricalValueModel
from pheno.prepare.agre_families import AgreLoader
from pheno.prepare.base_variables import BaseVariables


class PrepareVariables(AgreLoader, BaseVariables):

    INSTRUMENTS = [
        "ADIR1",
        "ADOS11", "ADOS21", "ADOS31", "ADOS41",
        "AffChild1",
        "AGRE_PhysMeas1",
        "FatherH1",
        "Hands1",
        "Language_Questionnaire1",
        "MotherH1",
        "Mullen1",
        "PhysExam1",
        "PPVT1",
        "PPVT_III1",
        "Raven1",
        "RBS1",
        "Repetitive_Behavior_Scales1",
        "SRS2_SRS20021",
        "SRS_2006_Preschool1",
        "SRS_20061",
        "Stanford_Binet1",
        "Unaffec1",
        "VABS-II1",
        "VINE1",
    ]

    def __init__(self, *args, **kwargs):
        super(PrepareVariables, self).__init__(*args, **kwargs)

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

    def prepare(self):
        self._create_variable_table()
        self._create_value_tables()

        persons = self.load_persons_df()
        for instrument in self.INSTRUMENTS:
            self._prepare_instrument(persons, instrument)

    def _prepare_instrument(self, persons, instrument_name):
        idf = self.load_instrument(instrument_name)
        df = idf.join(persons, on='person_id', rsuffix="_person")

        for measure_name in itertools.chain(df.columns[16:17],
                                            df.columns[20:len(idf.columns)]):
            print(measure_name)
            mdf = df[['person_id', measure_name,
                      'family_id', 'person_role']]
            self._build_variable(instrument_name, measure_name,
                                 mdf.dropna())

    def _build_variable(self, instrument_name, measure_name, mdf):
        measure_id = '{}.{}'.format(instrument_name, measure_name)
        print("building measure {}".format(measure_id))
        var = VariableModel()
        var.variable_id = measure_id
        var.table_name = instrument_name
        var.variable_name = measure_name

        self._classify_values(var, mdf)
        self.report_variable(var)
        self._save_variable(var, mdf)

        return var

    def _save_variable(self, var, mdf):
        if var.stats == self.CONTINUOUS:
            self._save_continuous_variable(var, mdf)
        elif var.stats == self.ORDINAL:
            self._save_ordinal_variable(var, mdf)
        elif var.stats == self.CATEGORICAL:
            self._save_categorical_variable(var, mdf)

    def _save_continuous_variable(self, var, mdf):
        assert var.min_value <= var.max_value
        with VariableManager(dbfile=self.get_dbfile()) as vm:
            vm.save(var)

        with ContinuousValueManager(dbfile=self.get_dbfile()) as vm:
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
        with VariableManager(dbfile=self.get_dbfile()) as vm:
            vm.save(var)

        with OrdinalValueManager(dbfile=self.get_dbfile()) as vm:
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
        with VariableManager(dbfile=self.get_dbfile()) as vm:
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

    @classmethod
    def check_type(cls, values):
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
        vtype = cls.check_type(values)
        if vtype == int:
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
                values_type == int or values_type == float:
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
                sorted(unique_values)
                var.value_domain = "{}".format(unique_values)
                return self.ORDINAL
            elif self.check_categorical_rank(rank, individuals):
                var.stats = self.CATEGORICAL
                sorted(unique_values)
                var.value_domain = "{}".format(unique_values)
                return self.CATEGORICAL
            else:
                var.stats = self.UNKNOWN
                var.value_domain = str(unique_values)
                return self.UNKNOWN

        elif values_type == str:
            if self.check_categorical_rank(rank, individuals):
                var.stats = self.CATEGORICAL
                sorted(unique_values)
                var.value_domain = "{}".format(unique_values)
                return self.CATEGORICAL

        var.stats = self.UNKNOWN
        var.value_domain = str(unique_values)
        return self.UNKNOWN
