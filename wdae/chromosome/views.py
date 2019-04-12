# from __future__ import unicode_literals
import pandas as pd

from rest_framework.views import APIView
from rest_framework.response import Response
from DAE import giDB


class ChromosomeView(APIView):
    def __init__(self):
        self.chromosomes = []

        csvfile = giDB.getChromosomesFile()
        reader = pd.read_csv(csvfile, delimiter='\t')

        reader['#chrom'] = reader['#chrom'].map(lambda x: x[3:])

        self.chromosomes.append({'name': '1', 'bands': []})
        for _, row in reader.iterrows():
            if self.chromosomes[-1]['name'] != row['#chrom']:
                self.chromosomes.append({'name': row['#chrom'], 'bands': []})
            self.chromosomes[-1]['bands'].append({
                'start': int(row['chromStart']),
                'end': int(row['chromEnd']),
                'name': row['name'],
                'gieStain': row['gieStain']
            })

    def get(self, request):
        return Response(self.chromosomes)
