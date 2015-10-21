'''
Created on Jun 18, 2015

@author: lubo
'''
from rest_framework.views import APIView
from rest_framework.response import Response
from api.views import prepare_query_dict, build_effect_type_filter
from api.logger import log_filter, LOGGER
from query_variants import do_query_variants, join_line
from api.dae_query import prepare_summary
from django.http.response import StreamingHttpResponse
import itertools
from rest_framework.parsers import JSONParser, FormParser
from rest_framework.authentication import TokenAuthentication, \
    BasicAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from query_prepare import prepare_ssc_filter
from api.query.wdae_query_variants import wdae_query_wrapper


class SSCPrepare(APIView):

    def prepare(self, request):
        data = prepare_query_dict(request.DATA)
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
                ['# %s' % comment]),
            content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=unruly.csv'
        response['Expires'] = '0'

        return response
