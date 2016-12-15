'''
Created on Dec 15, 2016

@author: lubo
'''
from pheno.prepare.base_variables import BaseVariables
from pheno.prepare.vip_families import VipLoader
# from pheno.models import VariableModel, VariableManager


class VipCommon(VipLoader, BaseVariables):

    def __init__(self, *args, **kwargs):
        super(VipCommon, self).__init__(*args, **kwargs)

#     def prepare_person_family_type_variable(self):
#         var = VariableModel()
#         var.variable_id = 'pheno_common.family_type'
#         var.table_name = 'pheno_common'
#         var.variable_name = 'family_type'
#         var.description = 'family type'
#         var.stats = 'categorical'
#         var.has_values = True
#
#         with VariableManager(config=self.config) as vm:
#             vm.save(var)
#
#         return var

    def prepare(self):
        idf = self.load_instrument('adi_r')
        persons = self.load_persons_df()

        df = idf.join(persons, on='person_id', rsuffix='_person')

        mdf = df[['person_id', 'family_type',
                  'family_id', 'person_role']]
        self._build_variable('pheno_common', 'family_type',
                             mdf.dropna())
