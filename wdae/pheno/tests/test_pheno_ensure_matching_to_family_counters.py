'''
Created on Nov 16, 2015

@author: lubo
'''
from rest_framework.test import APITestCase
import precompute
from families.counters import FamilyFilterCounters
from families.families_query import prepare_family_query, parse_family_ids
from pprint import pprint


def count_iterable(iterable):
    for num, _it in enumerate(iterable):
        pass
    return num + 1


class Test(APITestCase):

    def test_preview_view(self):
        data = {
            u'phenoMeasure': u'non_verbal_iq',
            u'denovoStudies': u'ALL SSC',
        }

        study_type, data = prepare_family_query(data)
        self.assertEquals('ALL', study_type)
        self.assertIn('familyIds', data)

        families_precompute = precompute.register.get(
            'families_precompute')
        families_buffer = families_precompute.families_buffer('ALL')
        counter = FamilyFilterCounters(families_buffer)

        self.assertIsNotNone(counter)

        family_ids = parse_family_ids(data)

        res = counter.count(family_ids)
        pprint(res)

        self.assertIsNotNone(res)
        self.assertEquals(2381, res['autism']['male'])
