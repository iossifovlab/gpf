'''
Created on Nov 16, 2015

@author: lubo
'''
from rest_framework import views, status
from rest_framework.response import Response
from api.logger import log_filter, LOGGER
from api.preloaded.register import get_register
from pheno.measures import NormalizedMeasure
from pheno.report import family_pheno_query_variants, pheno_merge_data, \
    pheno_calc
from django.http.response import StreamingHttpResponse
import itertools
from api.query.wdae_query_variants import prepare_query_dict


class PhenoViewBase(views.APIView):

    @staticmethod
    def istrue(val):
        return val == '1' or val == 'true' or val == 'True'

    @staticmethod
    def join_row(p, sep=','):
        r = [str(c) for c in p]
        return sep.join(r) + '\n'

    def normalize_by(self, data):
        norm_by = set()
        if 'normalizedBy' in data:
            norm_by = set(data['normalizedBy'].split(','))

        res = []
        if 'normByAge' in norm_by:
            res.append('age')
        if 'normByVIQ' in norm_by:
            res.append('verbal_iq')
        if 'normByNVIQ' in norm_by:
            res.append('non_verbal_iq')
        return res

    @staticmethod
    def prepare_query_dict(request):
        data = prepare_query_dict(request.data)
        print(data)
        if 'effectTypes' in data:
            print("deleting effect types")
            del data['effectTypes']
        return data

    def post(self, request):
        data = self.prepare_query_dict(request)

        LOGGER.info(log_filter(request, "download pheno report: " + str(data)))

        if 'phenoMeasure' not in data:
            LOGGER.error("phenoMeasure not found")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        measure_name = data['phenoMeasure']
        measures = get_register().get('pheno_measures')
        if not measures.has_measure(measure_name):
            return Response(status=status.HTTP_404_NOT_FOUND)

        by = self.normalize_by(data)
        nm = NormalizedMeasure(measure_name)
        nm.normalize(by=by)

        variants = family_pheno_query_variants(data)
        gender = measures.gender
        pheno = pheno_merge_data(variants, gender, nm)

        response = self.build_response(data, pheno)

        return response


class PhenoReportView(PhenoViewBase):

    def build_response(self, request, pheno):
        pheno.next()
        res = pheno_calc(pheno)
        response = {
            "data": res,
            "measure": "",
            "formula": "",
        }
        return Response(response)


class PhenoReportDownloadView(PhenoViewBase):

    def build_response(self, request, pheno):
        comment = ', '.join([': '.join([k, str(v)])
                             for (k, v) in request.items()
                             if k != 'effectTypes'])
        response = StreamingHttpResponse(
            itertools.chain(
                itertools.imap(self.join_row, pheno),
                ['# "%s"\n' % comment]),
            content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=pheno.csv'
        response['Expires'] = '0'
        return response


class PhenoMeasuresView(views.APIView):

    def get(self, request):
        register = get_register()
        measures = register.get('pheno_measures')
        return Response(measures.desc)
