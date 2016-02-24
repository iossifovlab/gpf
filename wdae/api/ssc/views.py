'''
Created on Jun 18, 2015

@author: lubo
'''
from rest_framework.views import APIView
from rest_framework.response import Response
from api.views import prepare_query_dict, build_effect_type_filter
from api.logger import log_filter, LOGGER
from query_variants import join_line
from api.dae_query import prepare_summary
from django.http.response import StreamingHttpResponse
import itertools
from rest_framework.parsers import JSONParser, FormParser
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from query_prepare import prepare_ssc_filter
from api.query.wdae_query_variants import wdae_query_wrapper
import api.preloaded


class SSCPrepare(APIView):

    @staticmethod
    def prepare_pheno_measure_query(data):
        if 'phenoMeasure' not in data:
            return data
        pheno_measure_query = data['phenoMeasure']
        del data['phenoMeasure']

        print(pheno_measure_query)
        assert isinstance(pheno_measure_query, dict)
        assert 'measure' in pheno_measure_query
        assert 'min' in pheno_measure_query
        assert 'max' in pheno_measure_query

        register = api.preloaded.register.get_register()
        assert register.has_key('pheno_measures')  # @IgnorePep8

        measures = register.get('pheno_measures')
        pheno_measure = pheno_measure_query['measure']
        assert measures.has_measure(pheno_measure)

        family_ids = measures.get_measure_families(
            pheno_measure,
            float(pheno_measure_query['min']),
            float(pheno_measure_query['max']))

        family_ids = [str(fid) for fid in family_ids]

        if 'familyIds' not in data:
            data['familyIds'] = ",".join(family_ids)
            print(data['familyIds'])
        else:
            family_ids = set(family_ids)
            print(family_ids)
            request_family_ids = set(data['familyIds'].split(','))
            result_family_ids = family_ids & request_family_ids
            data['familyIds'] = ",".join(result_family_ids)
        print(data['familyIds'])
        return data

    def prepare(self, request):
        data = dict(request.data)
        data = prepare_query_dict(data)
        data = self.prepare_pheno_measure_query(data)
        data = prepare_ssc_filter(data)
        build_effect_type_filter(data)
        return data


class SSCPreview(SSCPrepare):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        if request.method == 'OPTIONS':
            return Response()

        data = self.prepare(request)
        data['limit'] = 2000

        LOGGER.info(log_filter(request,
                               "ssc preview query variants: " + str(data)))

        generator = wdae_query_wrapper(data, atts=["_pedigree_", "phenoInChS"])
        summary = prepare_summary(generator)

        return Response(summary)


class SSCDownload(SSCPrepare):
    #     authentication_classes = (TokenAuthentication,
    #                               SessionAuthentication,
    #                               BasicAuthentication)
    #     permission_classes = (IsAuthenticated,)

    parser_classes = (JSONParser, FormParser,)

    def post(self, request):

        if request.method == 'OPTIONS':
            return Response()

        data = self.prepare(request)

        LOGGER.info(log_filter(request,
                               "ssc query variants request: " + str(data)))

        comment = ', '.join([': '.join([k, str(v)])
                             for (k, v) in data.items()])

        generator = wdae_query_wrapper(data)
        response = StreamingHttpResponse(
            itertools.chain(
                itertools.imap(join_line, generator),
                ['# "%s"' % comment]),
            content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=unruly.csv'
        response['Expires'] = '0'

        return response
