'''
Created on Jun 18, 2015

@author: lubo
'''
from builtins import map
from builtins import str
import itertools

from django.http.response import StreamingHttpResponse
from rest_framework.authentication import TokenAuthentication
from rest_framework.parsers import JSONParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from helpers.dae_query import prepare_summary
from helpers.wdae_query_variants import wdae_query_wrapper
from api.views import prepare_query_dict, build_effect_type_filter
from helpers.logger import log_filter, LOGGER
from query_variants import join_line
from ssc_families.views import SSCFamilyBase


class VIPPrepare(APIView, SSCFamilyBase):

    def prepare_vip_filter(self, data):
        if 'presentInParent' not in data:
            data['presentInParent'] = 'neither'

        if 'presentInChild' not in data:
            data['presentInChild'] = 'neither'

        if data['presentInParent'] == 'neither':
            data['transmittedStudies'] = 'None'
        else:
            data['transmittedStudies'] = 'VIP-JHC'  # FIXME

        if data['presentInChild'] == 'neither':
            data['denovoStudies'] = 'None'
        else:
            data['denovoStudies'] = 'VIP-JHC'  # FIXME

        if 'phenoType' in data:
            del data['phenoType']

        return data

    def __init__(self):
        SSCFamilyBase.__init__(self)
        APIView.__init__(self)

    def prepare(self, request):
        data = prepare_query_dict(request.data)

        # _fst, data = prepare_family_query(data)

        families = self.prepare_families(data)
        if families:
            data['familyIds'] = ','.join(families['all'])

        data = self.prepare_vip_filter(data)
        build_effect_type_filter(data)
        return data


class VIPPreview(VIPPrepare):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        if request.method == 'OPTIONS':
            return Response()

        data = self.prepare(request)
        data['limit'] = 2000

        LOGGER.info(log_filter(request,
                               "vip preview query variants: " + str(data)))

        generator = wdae_query_wrapper(
            data, atts=["_pedigree_", "phenoInChS"])
        summary = prepare_summary(generator)

        return Response(summary)


class VIPDownload(VIPPrepare):
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
                               "vip query variants request: " + str(data)))

        comment = ', '.join([': '.join([k, str(v)])
                             for (k, v) in list(data.items())])

        generator = wdae_query_wrapper(data)
        response = StreamingHttpResponse(
            itertools.chain(
                list(map(join_line, generator)),
                ['# "%s"' % comment]),
            content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=unruly.csv'
        response['Expires'] = '0'

        return response
