'''
Created on Nov 16, 2015

@author: lubo
'''
import itertools
import numpy as np

from django.http.response import StreamingHttpResponse
from rest_framework import views, status
from rest_framework.response import Response

from preloaded.register import get_register
from api.query.wdae_query_variants import prepare_query_dict
from pheno.measures import NormalizedMeasure
from pheno.report import family_pheno_query_variants, pheno_calc
from helpers.logger import log_filter, LOGGER
from families.families_query import prepare_family_query


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
        if 'effectTypes' in data:
            del data['effectTypes']
        _fst, data = prepare_family_query(data)

        return data

    def post(self, request):
        data = self.prepare_query_dict(request)

        LOGGER.info(log_filter(request, "pheno report: " + str(data)))

        if 'phenoMeasure' not in data:
            LOGGER.error("phenoMeasure not found")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        measure_name = data['phenoMeasure']
        measures = get_register().get('pheno_measures')
        if not measures.has_measure(measure_name):
            return Response(status=status.HTTP_404_NOT_FOUND)
        if 'familyIds' in data:
            families_query = set(data['familyIds'].split(','))
        else:
            families_query = None

        by = self.normalize_by(data)
        nm = NormalizedMeasure(measure_name)
        nm.normalize(by=by)

        variants = family_pheno_query_variants(data)
        pheno = measures.pheno_merge_data(variants, nm, families_query)

        response = self.build_response(data, pheno, nm)
        return response


class PhenoReportView(PhenoViewBase):

    def build_response(self, request, pheno, nm):
        pheno.next()
        res = pheno_calc(pheno)
        response = {
            "data": res,
            "measure": nm.measure,
            "formula": nm.formula,
        }
        return Response(response)


class PhenoReportDownloadView(PhenoViewBase):

    def build_response(self, request, pheno, nm):
        comment = ', '.join([': '.join([k, str(v)])
                             for (k, v) in request.items()
                             if k != 'effectTypes'])
        # comment.append(formula)

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


class PhenoMeasureHistogramView(views.APIView):

    def __init__(self):
        self.measures = get_register().get('pheno_measures')

    def post(self, request):
        data = request.data

        assert "measure" in data
        assert self.measures is not None

        pheno_measure = data['measure']
        if not self.measures.has_measure(pheno_measure):
            return Response(status=status.HTTP_404_NOT_FOUND)

        df = self.measures.get_measure_df(pheno_measure)
        m = df[pheno_measure]
        bars, bins = np.histogram(
            df[np.logical_not(np.isnan(m.values))][pheno_measure].values, 25)

        result = {
            "measure": pheno_measure,
            "desc": "",
            "min": m.min(),
            "max": m.max(),
            "bars": bars,
            "bins": bins,
            "step": (m.max() - m.min()) / 1000.0,
        }
        return Response(result, status=status.HTTP_200_OK)


class PhenoMeasurePartitionsView(views.APIView):

    def __init__(self):
        self.measures = get_register().get('pheno_measures')

    def post(self, request):
        data = request.data

        assert "measure" in data
        assert self.measures is not None

        pheno_measure = data['measure']

        if not self.measures.has_measure(pheno_measure):
            return Response(status=status.HTTP_404_NOT_FOUND)

        df = self.measures.get_measure_df(pheno_measure)
        mmin = float(data["min"])
        mmax = float(data["max"])

        total = 1.0 * len(df)

        ldf = df[df[pheno_measure] < mmin]
        rdf = df[df[pheno_measure] > mmax]
        mdf = df[np.logical_and(df[pheno_measure] >= mmin,
                                df[pheno_measure] <= mmax)]

        res = {"measure": pheno_measure,
               "min": mmin,
               "max": mmax,
               "left": {"count": len(ldf), "percent": len(ldf) / total},
               "mid": {"count": len(mdf), "percent": len(mdf) / total},
               "right": {"count": len(rdf), "percent": len(rdf) / total}}
        return Response(res)
