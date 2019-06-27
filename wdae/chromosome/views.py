# from __future__ import unicode_literals
import pandas as pd

from rest_framework.views import APIView
from rest_framework.response import Response
from datasets_api.studies_manager import get_studies_manager


class ChromosomeView(APIView):
    def __init__(self):
        gene_info_config = get_studies_manager().get_gene_info_config()
        self.chromosomes = []

        csvfile = gene_info_config.chromosomes.file
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
