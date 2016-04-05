'''
Created on Mar 23, 2016

@author: lubo
'''
from rest_framework.views import APIView
import precompute
from families.counters import FamilyFilterCounters
from families.families_query import prepare_family_query
from rest_framework.response import Response


class FamilyFilterCountersView(APIView):

    def __init__(self):
        families_precompute = precompute.register.get('families_precompute')
        self.families_buffer = families_precompute.families_buffer()
        self.families_counters = families_precompute.families_counters()
        self.counter = FamilyFilterCounters(self.families_buffer)

    def post(self, request):
        data = request.data
        data = prepare_family_query(data)
        if 'familyIds' not in data:
            return Response(self.families_counters)

        assert 'familyIds' in data

        family_ids = data['familyIds'].split(',')
        print("family_ids: {}".format(family_ids))
        result = self.counter.count(family_ids)

        return Response(result)
