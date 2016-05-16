'''
Created on Jun 18, 2015

@author: lubo
'''
from rest_framework.views import APIView
from rest_framework.response import Response
from api.views import build_effect_type_filter
from helpers.logger import log_filter, LOGGER
from query_variants import join_line
from api.dae_query import prepare_summary
from django.http.response import StreamingHttpResponse
import itertools
from rest_framework.parsers import JSONParser, FormParser
from api.query.wdae_query_variants import wdae_query_wrapper, \
    prepare_query_dict


class SequencingDenovoPrepare(APIView):

    def prepare(self, request):
        data = prepare_query_dict(request.data)
        data['denovoStudies'] = "ALL WHOLE EXOME"
        data['transmittedStudies'] = None

        build_effect_type_filter(data)
        return data


class SequencingDenovoPreview(SequencingDenovoPrepare):

    def post(self, request):

        if request.method == 'OPTIONS':
            return Response()

        data = self.prepare(request)
        data['limit'] = 2000

        LOGGER.info(log_filter(request,
                               "sd preview query variants: " + str(data)))

        generator = wdae_query_wrapper(data,
                                       atts=["_pedigree_", "phenoInChS"])
        summary = prepare_summary(generator)

        return Response(summary)


class SequencingDenovoDownload(SequencingDenovoPrepare):

    parser_classes = (JSONParser, FormParser,)

    def post(self, request):
        if request.method == 'OPTIONS':
            return Response()

        data = self.prepare(request)

        LOGGER.info(log_filter(request,
                               "sd query variants request: " + str(data)))

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
