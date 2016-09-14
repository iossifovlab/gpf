'''
Created on Sep 14, 2016

@author: lubo
'''
from pheno.utils.load_raw import V14Loader, V15Loader
from pheno.models import VariableModel, RawValueManager, PersonManager,\
    PersonModel
from pheno.precompute.values import PrepareRawValues
from pheno.utils.commons import calc_race


class PreparePhenoCommonAge(V14Loader):

    def __init__(self, *args, **kwargs):
        super(PreparePhenoCommonAge, self).__init__(*args, **kwargs)

    def prepare_person_age_variable(self):
        var = VariableModel()
        var.variable_id = 'pheno_common.age'
        var.table_name = 'pheno_common'
        var.variable_name = 'age'
        var.domain = 'meta_t.integer'
        var.domain_choice_label = None
        var.measurement_scale = 'integer'
        var.description = 'Age at assessment'
        var.has_values = True

        with VariableModel() as vm:
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
        var.domain = 'meta_t.text'
        var.domain_choice_label = None
        var.measurement_scale = 'text'
        var.description = 'Race'
        var.has_values = True

        with VariableModel() as vm:
            vm.save(var)

        return var

    def _prepare_probands_race(self, variable):
        with RawValueManager(config=self.config) as vm:
            df = vm.load_df(
                where="variable_id='{}'"
                .format('ssc_core_descriptive.race'))

        names = df.columns.tolist()
        names[names.index('person_id')] = 'individual'
        names[names.index('value')] = 'race'
        df.columns = names

        prep = PrepareRawValues()
        prep.prepare_variable(variable, [df])

#         with PersonManager(config=self.config) as pm:
#             # print('setting race for {}'.format(row['person_id']))
#             for _index, row in df.iterrows():
#                 person = pm.get(
#                     where="person_id='{}'".format(row['person_id']))
#                 person.race = row['value']
#                 pm.save(person)
# 
#     def _prepare_parents_race(self):
#         with RawValueManager(config=self.config) as vm:
#             df = vm.load_df(
#                 where="variable_id='{}'"
#                 .format('ssc_commonly_used.race_parents'))
#         with PersonManager(config=self.config) as pm:
#             # print('setting race for {}'.format(row['person_id']))
#             for _index, row in df.iterrows():
#                 person = pm.get("person_id='{}'".format(row['person_id']))
#                 person.race = row['value']
#                 pm.save(person)
# 
#     def _prepare_siblings_race(self):
#         with PersonManager(config=self.config) as pm:
#             siblings = pm.load_df(where="role='sib'")
#             for _index, row in siblings.iterrows():
#                 sib = PersonModel.create_from_df(row)
#                 mom = pm.get(where="person_id='{}.mo'".format(sib.family_id))
#                 dad = pm.get(where="person_id='{}.fa'".format(sib.family_id))
#                 sib.race = calc_race(mom.race, dad.race)
#                 pm.save(sib)
# 
#     def _check_probands_race(self):
#         with PersonManager(config=self.config) as pm:
#             probands = pm.load_df(where="role='prb'")
#             for _index, row in probands.iterrows():
#                 prb = PersonModel.create_from_df(row)
#                 mom = pm.get(where="person_id='{}.mo'".format(prb.family_id))
#                 dad = pm.get(where="person_id='{}.fa'".format(prb.family_id))
#                 race = calc_race(mom.race, dad.race)
#                 if prb.race != race:
#                     print("family: {}; prb: |{}|; mom: |{}|; dad: |{}|".format(
#                         prb.family_id, prb.race, mom.race, dad.race))

    def prepare(self):
        variable = self.prepare_person_race_variable()
        self._prepare_probands_race(variable)
        
#         self._prepare_probands_race()
#         self._prepare_parents_race()
#         self._prepare_siblings_race()
#         self._check_probands_race()
