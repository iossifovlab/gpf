# from __future__ import unicode_literals
from builtins import next
import csv

from rest_framework.views import APIView
from rest_framework.response import Response
from DAE import giDB


class ChromosomeView(APIView):
    def __init__(self):
        self.chromosomes = []
        with open(giDB.getChromosomesFile(), 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            next(reader)
            self.chromosomes.append({'name': '1', 'bands': []})
            for row in reader:
                if self.chromosomes[-1]['name'] != row[0][3:]:
                    self.chromosomes.append({'name': row[0][3:], 'bands': []})
                self.chromosomes[-1]['bands'].append({
                    'start': int(row[1]),
                    'end': int(row[2]),
                    'name': row[3],
                    'gieStain': row[4]
                })

    def get(self, request):
        return Response(self.chromosomes)
