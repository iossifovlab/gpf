'''
Created on Sep 14, 2016

@author: lubo
'''
import pandas as pd

from pheno.utils.load_raw import V14Loader, V15Loader
from pheno.models import VariableModel, RawValueManager, PersonManager,\
    PersonModel, VariableManager
from pheno.prepare.values import PrepareRawValues
from pheno.utils.commons import calc_race


class PreparePhenoCommonAge(V14Loader):

    def __init__(self, *args, **kwargs):
        super(PreparePhenoCommonAge, self).__init__(*args, **kwargs)

    def prepare_person_age_variable(self):
        var = VariableModel()
        var.variable_id = 'pheno_common.age'
        var.table_name = 'pheno_common'
        var.variable_name = 'age'
        var.domain = 'meta.integer_t'
        var.domain_choice_label = None
        var.measurement_scale = 'integer'
        var.description = 'Age at assessment'
        var.has_values = True

        with VariableManager(config=self.config) as vm:
            vm.save(var)

        return var

    def prepare(self):
        variable = self.prepare_person_age_variable()
        df = self.load_df('ssc_age_at_assessment.csv')

        names = df.columns.tolist()
        names[names.index('portalId')] = 'individual'
        names[names.index('age_at_assessment')] = 'age'
        df.columns = names

        prep = PrepareRawValues()
        prep.prepare_variable(variable, [df])


class PreparePhenoCommonRace(V15Loader):

    def __init__(self, *args, **kwargs):
        super(PreparePhenoCommonRace, self).__init__(*args, **kwargs)

    def prepare_person_race_variable(self):
        var = VariableModel()
        var.variable_id = 'pheno_common.race'
        var.table_name = 'pheno_common'
        var.variable_name = 'race'
        var.domain = 'meta.text_t'
        var.domain_choice_label = None
        var.measurement_scale = 'text'
        var.description = 'Race'
        var.has_values = True

        with VariableManager(config=self.config) as vm:
            vm.save(var)

        return var

#     def _prepare_probands_race(self, variable):
#         with RawValueManager(config=self.config) as vm:
#             df = vm.load_df(
#                 where="variable_id='{}'"
#                 .format('ssc_core_descriptive.race'))
#
#         names = df.columns.tolist()
#         names[names.index('person_id')] = 'individual'
#         names[names.index('value')] = 'race'
#         df.columns = names
#
#         prep = PrepareRawValues()
#         prep.prepare_variable(variable, [df])

    def _prepare_parents_race(self, variable):
        with RawValueManager(config=self.config) as vm:
            df = vm.load_df(
                where="variable_id='{}'"
                .format('ssc_commonly_used.race_parents'))

        names = df.columns.tolist()
        names[names.index('person_id')] = 'individual'
        names[names.index('value')] = 'race'
        df.columns = names

        prep = PrepareRawValues()
        prep.prepare_variable(variable, [df])

    def _parent_races(self):
        with RawValueManager(config=self.config) as vm:
            moms = vm.load(
                where="variable_id='pheno_common.race' and person_role='mom'")
            dads = vm.load(
                where="variable_id='pheno_common.race' and person_role='dad'")
        moms = dict([(m.person_id, m.value) for m in moms])
        dads = dict([(d.person_id, d.value) for d in dads])
        assert abs(len(moms) - len(dads)) < 100

        return moms, dads

    def _prepare_siblings_race(self, variable):
        moms, dads = self._parent_races()

        with PersonManager(config=self.config) as pm:
            siblings = pm.load_df(where="role='sib'")
            siblings.loc[:, 'value'] = pd.Series('', index=siblings.index)

            for _index, row in siblings.iterrows():
                sib = PersonModel.create_from_df(row)
                mom_race = moms.get('{}.mo'.format(sib.family_id), None)
                dad_race = dads.get('{}.fa'.format(sib.family_id), None)
                row['value'] = calc_race(mom_race, dad_race)

        names = siblings.columns.tolist()
        names[names.index('person_id')] = 'individual'
        names[names.index('value')] = 'race'
        siblings.columns = names

        prep = PrepareRawValues()
        prep.prepare_variable(variable, [siblings])

    def _prepare_probands_race(self, variable):
        moms, dads = self._parent_races()

        with PersonManager(config=self.config) as pm:
            probands = pm.load_df(where="role='prb'")
            probands.loc[:, 'value'] = pd.Series('', index=probands.index)

            for _index, row in probands.iterrows():
                prb = PersonModel.create_from_df(row)
                mom_race = moms.get('{}.mo'.format(prb.family_id), None)
                dad_race = dads.get('{}.fa'.format(prb.family_id), None)
                row['value'] = calc_race(mom_race, dad_race)

        names = probands.columns.tolist()
        names[names.index('person_id')] = 'individual'
        names[names.index('value')] = 'race'
        probands.columns = names

        prep = PrepareRawValues()
        prep.prepare_variable(variable, [probands])

    def _proband_races(self):
        with RawValueManager(config=self.config) as vm:
            prbs_races = vm.load(
                where="variable_id='pheno_common.race' and person_role='prb'")
        prbs_races = dict([(p.person_id, p.value) for p in prbs_races])
        return prbs_races

#     def _check_probands_race(self):
#         moms_races, dads_races = self._parent_races()
#
#         prbs_races = self._proband_races()
#
#         with PersonManager(config=self.config) as pm:
#             probands = pm.load_df(where="role='prb'")
#             for _index, row in probands.iterrows():
#                 prb = PersonModel.create_from_df(row)
#                 prb_race = prbs_races.get(row['person_id'], None)
#                 mom_race = moms_races.get(
#                     '{}.mo'.format(row['family_id']), None)
#                 dad_race = dads_races.get(
#                     '{}.fa'.format(row['family_id']), None)
#                 race = calc_race(mom_race, dad_race)
#                 if prb_race != race:
#                     print(
#                        "family: {}; prb: |{}|; mom: |{}|; dad: |{}|".format(
#                         prb.family_id, prb_race, mom_race, dad_race))

    def prepare(self):
        variable = self.prepare_person_race_variable()
        self._prepare_parents_race(variable)
        self._prepare_probands_race(variable)
        self._prepare_siblings_race(variable)
        # self._check_probands_race()


class PreparePhenoIQ(V15Loader):
    NONVERBAL_IQ = 'ssc_core_descriptive.ssc_diagnosis_nonverbal_iq'
    VERBAL_IQ = 'ssc_core_descriptive.ssc_diagnosis_verbal_iq'

    def prepare_pheno_non_verbal_iq_variables(self):
        var = VariableModel()
        var.variable_id = 'pheno_common.non_verbal_iq'
        var.table_name = 'pheno_common'
        var.variable_name = 'non_verbal_iq'
        var.domain = 'meta.float_t'
        var.domain_choice_label = None
        var.measurement_scale = 'float'
        var.description = 'Non verbal IQ'
        var.has_values = True

        with VariableManager(config=self.config) as vm:
            vm.save(var)

        return var

    def prepare_pheno_verbal_iq_variables(self):
        var = VariableModel()
        var.variable_id = 'pheno_common.verbal_iq'
        var.table_name = 'pheno_common'
        var.variable_name = 'verbal_iq'
        var.domain = 'meta.float_t'
        var.domain_choice_label = None
        var.measurement_scale = 'float'
        var.description = 'Verbal IQ'
        var.has_values = True

        with VariableManager(config=self.config) as vm:
            vm.save(var)

        return var

    def _prepare_nonverbal_iq(self, variable):
        with RawValueManager(config=self.config) as vm:
            df = vm.load_df(where="variable_id='{}'".format(self.NONVERBAL_IQ))

        names = df.columns.tolist()
        names[names.index('person_id')] = 'individual'
        names[names.index('value')] = 'non_verbal_iq'
        df.columns = names

        prep = PrepareRawValues()
        prep.prepare_variable(variable, [df])

    def _prepare_verbal_iq(self, variable):
        with RawValueManager(config=self.config) as vm:
            df = vm.load_df(where="variable_id='{}'".format(self.VERBAL_IQ))

        names = df.columns.tolist()
        names[names.index('person_id')] = 'individual'
        names[names.index('value')] = 'verbal_iq'
        df.columns = names

        prep = PrepareRawValues()
        prep.prepare_variable(variable, [df])

    def prepare(self):
        nviq_variable = self.prepare_pheno_non_verbal_iq_variables()
        self._prepare_nonverbal_iq(nviq_variable)

        viq_variable = self.prepare_pheno_verbal_iq_variables()
        self._prepare_verbal_iq(viq_variable)
