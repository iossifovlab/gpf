'''
Created on Jun 18, 2015

@author: lubo
'''
from rest_framework.views import APIView
from rest_framework.response import Response
from api.views import prepare_query_dict, build_effect_type_filter
from api.logger import log_filter, LOGGER
from api.query.query_variants import do_query_variants, join_line
from api.dae_query import prepare_summary
from django.http.response import StreamingHttpResponse
import itertools
from rest_framework.parsers import JSONParser, FormParser


class SequencingDenovoPrepare(APIView):
    
    def prepare(self, request):
        data = prepare_query_dict(request.DATA)
        data['denovoStudies'] = "ALL WHOLE EXOME"
        data['transmittedStudies'] = None

        build_effect_type_filter(data)
        return data


class SequencingDenovoPreview(SequencingDenovoPrepare):
    
    def post(self,request):
        if request.method == 'OPTIONS':
            return Response()
    
        data = self.prepare(request)
        
        LOGGER.info(log_filter(request, "preview query variants: " + str(data)))
    
        generator = do_query_variants(data, atts=["_pedigree_", "phenoInChS"])
        summary = prepare_summary(generator)
    
        return Response(summary)

    
class SequencingDenovoDownload(SequencingDenovoPrepare):
    
    parser_classes = (JSONParser, FormParser,)
    
    def post(self, request):
        
        if request.method == 'OPTIONS':
            return Response()
    
        data = self.prepare(request)
            
        LOGGER.info(log_filter(request, "query variants request: " + str(data)))
    
        comment = ', '.join([': '.join([k, str(v)]) for (k, v) in data.items()])
    
        generator = do_query_variants(data)
        response = StreamingHttpResponse(
            itertools.chain(
                itertools.imap(join_line, generator),
                ['# %s' % comment]),
            content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=unruly.csv'
        response['Expires'] = '0'
    
        return response