import pandas as pd

from rest_framework.response import Response

from query_base.query_base import QueryBaseView


class ChromosomeView(QueryBaseView):

    def __init__(self):
        super(ChromosomeView, self).__init__()

        gene_info_config = self.gpf_instance.gene_info_config
        self.chromosomes = []

        csvfile = gene_info_config.chromosomes.file
        reader = pd.read_csv(csvfile, delimiter='\t')

        reader['#chrom'] = reader['#chrom'].map(lambda x: x[3:])
        col_rename = {'chromStart': 'start', 'chromEnd': 'end'}
        reader = reader.rename(columns=col_rename)

        cols = ['start', 'end', 'name', 'gieStain']
        reader['start'] = pd.to_numeric(reader['start'], downcast='integer')
        reader['end'] = pd.to_numeric(reader['end'], downcast='integer')
        reader = reader.groupby('#chrom')[cols] \
                       .apply(lambda x: x.to_dict(orient='records')) \
                       .to_dict()

        self.chromosomes = [{'name': k, 'bands': v} for k, v in reader.items()]

    def get(self, request):
        return Response(self.chromosomes)
