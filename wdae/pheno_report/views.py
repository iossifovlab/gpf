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
from helpers.logger import log_filter, LOGGER
from pheno_families.views import PhenoFamilyBase
from pheno_report import pheno_request, pheno_tool


class PhenoViewBase(views.APIView, PhenoFamilyBase):

    def __init__(self):
        PhenoFamilyBase.__init__(self)

    @staticmethod
    def istrue(val):
        return val == '1' or val == 'true' or val == 'True'

    @staticmethod
    def join_row(p, sep=','):
        r = [str(c) for c in p]
        return sep.join(r) + '\n'

    def post(self, request):
        LOGGER.info(log_filter(request, "pheno_report report request: " +
                               str(request.data)))

        try:
            req = pheno_request.Request(request.data)
            tool = pheno_tool.PhenoTool(req)

            response = self.build_response(tool)
            return response

        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class PhenoReportView(PhenoViewBase):

    @staticmethod
    def migrate_response(response):
        result = []
        for r in response:
            result.append(
                (
                    r['effectType'],
                    r['gender'],
                    r['negativeMean'],
                    r['negativeDeviation'],
                    r['positiveMean'],
                    r['positiveDeviation'],
                    r['pValue'],
                    r['positiveCount'],
                    r['negativeCount'],
                )
            )
        return result

    def build_response(self, tool):
        res = tool.calc()
        response = {
            "data": self.migrate_response(res),
            "measure": tool.nm.measure_id,
            "formula": tool.nm.formula,
        }
        return Response(response)


class PhenoReportDownloadView(PhenoViewBase):

    def build_response(self, tool):
        table = tool.build_data_table()
        response = StreamingHttpResponse(
            itertools.chain(
                itertools.imap(self.join_row, table),),
            content_type='text/csv')
        response['Content-Disposition'] = \
            'attachment; filename=pheno_report.csv'
        response['Expires'] = '0'
        return response


class PhenoMeasuresView(views.APIView):

    def get(self, request):
        register = get_register()
        measures = register.get('pheno_measures')
        return Response(measures.load_desc().values())


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

        assert self.measures is not None

        if 'measure' not in data:
            return Response(status=status.HTTP_400_BAD_REQUEST)

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


class PhenoEffectTypeGroups(views.APIView):
    effect_type_groups = ['LGDs', 'Nonsense', 'Frame-shift', 'Splice-site',
                          'Missense', 'Nonsynonymous', 'Synonymous',
                          'CNV', 'CNV+', 'CNV-', ]

    def get(self, request):
        return Response(self.effect_type_groups)


class PhenoEffectTypeGroupsGrouped(views.APIView):
    effect_type_groups = {
        'groups': [
            ['LGDs', 'Nonsense', 'Frame-shift', 'Splice-site'],
            ['Missense', 'Nonsynonymous', 'Synonymous'],
            ['CNV', 'CNV+', 'CNV-', ]
        ],
        'defaults': ['LGDs', 'Missense', 'Synonymous', 'CNV'],
    }

    def get(self, request):
        return Response(self.effect_type_groups)
