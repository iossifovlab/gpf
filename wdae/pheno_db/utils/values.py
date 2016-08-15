'''
Created on Aug 15, 2016

@author: lubo
'''
from pheno_db.models import ValueFloat


class ValuesLoader(object):

    def __init__(self, variable):
        assert variable.measurement_scale == 'float'

        self.variable = variable
        self.model = ValueFloat

    def load_qs(self):
        qs = self.model.objects.filter(descriptor=self.variable)
        return qs

    def load_df(self):
        pass
