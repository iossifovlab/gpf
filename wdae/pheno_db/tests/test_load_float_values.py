'''
Created on Aug 15, 2016

@author: lubo
'''
from django.test import TestCase

from pheno_db.models import VariableDescriptor
from pheno_db.utils.values import ValuesLoader


class Test(TestCase):
    fixtures = [
        'variable_descriptor.json',
        'value_float.json',
    ]

    def setUp(self):
        self.vd = VariableDescriptor.objects.get(
            variable_id='ssc_hwhc.head_circumference'
        )

    def test_check_variable_descriptor(self):
        self.assertIsNotNone(self.vd)

    def test_value_float_qs(self):
        loader = ValuesLoader(self.vd)
        qs = loader.load_qs()
        rows = list(qs)
        print(rows)
        self.assertEquals(6, len(rows))
