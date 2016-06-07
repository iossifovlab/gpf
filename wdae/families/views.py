'''
Created on Mar 23, 2016

@author: lubo
'''
from rest_framework.views import APIView
import precompute
from families.counters import FamilyFilterCounters
from families.families_query import prepare_family_query
from rest_framework.response import Response
from helpers.logger import log_filter, LOGGER
from api.default_ssc_study import get_ssc_denovo


class FamilyFilterCountersView(APIView):

    def __init__(self):
        self.families_precompute = precompute.register.get(
            'families_precompute')

    def post(self, request):
        data = request.data
        LOGGER.info(log_filter(request, "family counters request: " +
                               str(data)))

        study_type, data = prepare_family_query(data)
        if 'familyIds' not in data:
            families_counters = self.families_precompute.families_counters(
                study_type)
            return Response(families_counters)

        assert 'familyIds' in data

        families_buffer = self.families_precompute.families_buffer(study_type)
        self.counter = FamilyFilterCounters(families_buffer)

        family_ids = data['familyIds'].split(',')
        result = self.counter.count(family_ids)

        return Response(result)


class FamilyFilterStudies(APIView):

    def get(self, request):
        result = ["All"]
        result.extend(get_ssc_denovo().split(','))
        return Response(result)
