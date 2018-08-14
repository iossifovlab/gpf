from __future__ import unicode_literals
from rest_framework.views import APIView
from rest_framework.response import Response

from preloaded import register


class GenomicScoresView(APIView):

    def get(self, request):
        scores = register.get('genomic_scores')
        return Response(scores.desc)
