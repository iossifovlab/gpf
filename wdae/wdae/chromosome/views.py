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

        cols = ['chromStart', 'chromEnd', 'name', 'gieStain']
        reader = reader.groupby('#chrom')[cols] \
                       .apply(lambda x: x.values.tolist()) \
                       .to_dict()

        for k, v in reader.items():
            bands = []
            for band in v:  # Maybe find a way to do this with pandas
                bands.append({
                    'start': int(band[0]),
                    'end': int(band[1]),
                    'name': band[2],
                    'gieStain': band[3]
                })

            self.chromosomes.append({'name': k, 'bands': bands})

    def get(self, request):
        return Response(self.chromosomes)
