'''
Created on Aug 15, 2016

@author: lubo
'''
import pandas as pd
from pheno_db.models import ValueFloat


class ValuesLoader(object):
    fieldnames = [
        'family_id',
        'person_id',
        'person_role',
        'variable_id',
        'value',
    ]

    def __init__(self, variable):
        assert variable.measurement_scale == 'float'

        self.variable = variable
        self.model = ValueFloat

    def load_qs(self):
        qs = self.model.objects.filter(descriptor=self.variable)
        return qs

    def load_df(self):
        qs = self.load_qs()
        recs = list(qs.values_list(*self.fieldnames))
        df = pd.DataFrame.from_records(recs, columns=self.fieldnames)
        df.variable_descriptor = self.variable

        return df
