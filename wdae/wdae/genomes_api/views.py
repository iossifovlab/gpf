from itertools import islice

from rest_framework.response import Response
from rest_framework import status

from query_base.query_base import QueryBaseView


class DefaultGeneModelsId(QueryBaseView):
    def get(self, request):
        default_gene_models_id = \
            self.gpf_instance.dae_config.gene_models.resource_id
        return Response(default_gene_models_id, status=status.HTTP_200_OK)


class GeneModels(QueryBaseView):
    def get(self, request, gene_symbol):
        gene_models = self.gpf_instance.gene_models.gene_models
        if gene_symbol not in gene_models:
            return Response(None, status=status.HTTP_404_NOT_FOUND)
        else:
            transcripts = gene_models[gene_symbol]
            response_data = {
                "gene": gene_symbol,
                "transcripts": [],
            }
            for tr in transcripts:
                response_data["transcripts"].append(
                    self.transcript_to_dict(tr)
                )

            return Response(
                response_data,
                status=status.HTTP_200_OK,
            )

    def transcript_to_dict(self, transcript):
        output = dict()
        output["transcript_id"] = transcript.tr_id
        output["strand"] = transcript.strand
        output["chrom"] = transcript.chrom
        output["cds"] = self.cds_to_dictlist(transcript.cds)
        output["utr3"] = list()
        for region in transcript.UTR3_regions():
            output["utr3"].append(self.region_to_dict(region))
        output["utr5"] = list()
        for region in transcript.UTR5_regions():
            output["utr5"].append(self.region_to_dict(region))
        output["exons"] = list()
        for exon in transcript.exons:
            output["exons"].append(self.exon_to_dict(exon))
        return output

    def cds_to_dictlist(self, cds):
        return [
            {"start": a, "stop": b}
            for (a, b) in zip(cds[::2], cds[1::2])
        ]

    def region_to_dict(self, region):
        return {
            "start": region.start,
            "stop": region.stop
        }

    def exon_to_dict(self, exon):
        return {
            "start": exon.start,
            "stop": exon.stop
        }


class GeneSymbolsSearch(QueryBaseView):

    RESPONSE_LIMIT = 20

    def get(self, request, search_term):
        gene_models = self.gpf_instance.gene_models.gene_models

        matching_gene_symbols = filter(
            lambda gs: gs.startswith(search_term),
            gene_models.keys()
        )

        matching_gene_symbols = islice(
            matching_gene_symbols, None, self.RESPONSE_LIMIT
        )

        return Response(
            {"gene_symbols": list(matching_gene_symbols)},
            status=status.HTTP_200_OK,
        )
