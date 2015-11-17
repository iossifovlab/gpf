'''
Created on Nov 16, 2015

@author: lubo
'''
from rest_framework import views, status
from rest_framework.response import Response
from api.logger import log_filter, LOGGER
from api.views import prepare_query_dict
from api.preloaded.register import get_register
from pheno.measures import NormalizedMeasure
from pheno.report import family_pheno_query_variants, pheno_merge_data, \
    pheno_calc


class PhenoReportView(views.APIView):

    @staticmethod
    def istrue(val):
        return val == '1' or val == 'true' or val == 'True'

    def normalize_by(self, data):
        res = []
        if 'normByAge' in data and self.istrue(data['normByAge']):
            res.append('age')
        if 'normByVIQ' in data and self.istrue(data['normByVIQ']):
            res.append('verbal_iq')
        if 'normByNVIQ' in data and self.istrue(data['normByNVIQ']):
            res.append('non_verbal_iq')
        return res

    def post(self, request):
        data = prepare_query_dict(request.data)
        LOGGER.info(log_filter(request, "preview pheno report: " + str(data)))

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
        pheno.next()
        res = pheno_calc(pheno)
        data = {
            "data": res,
            "measure": measure_name,
            "formula": nm.formula,
        }
        return Response(data)


class PhenoMeasuresView(views.APIView):

    def get(self, request):
        register = get_register()
        measures = register.get('pheno_measures')
        return Response(measures.desc)
