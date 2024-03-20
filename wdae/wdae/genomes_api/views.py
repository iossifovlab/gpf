from itertools import islice
from typing import Any

from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status

from query_base.query_base import QueryBaseView

from dae.genomic_resources.gene_models import TranscriptModel, Exon
from dae.utils.regions import Region


class DefaultGeneModelsId(QueryBaseView):
    def get(self, _request: Request) -> Response:
        default_gene_models_id = \
            self.gpf_instance.dae_config.gene_models.resource_id
        return Response(default_gene_models_id, status=status.HTTP_200_OK)


class GeneModels(QueryBaseView):
    """Process gene model response."""

    def get(self, _request: Request, gene_symbol: str) -> Response:
        """Return gene mode corresponding to a gene symbol."""
        gene_symbol, transcript_models = \
            self.gpf_instance.get_transcript_models(gene_symbol)

        if not transcript_models:
            return Response(status=status.HTTP_404_NOT_FOUND)

        response_data = {
            "gene": gene_symbol,
            "transcripts": [],
        }
        for transcript in transcript_models:
            response_data["transcripts"].append(
                self.transcript_to_dict(transcript)
            )

        if response_data["transcripts"]:
            return Response(
                response_data,
                status=status.HTTP_200_OK,
            )

        return Response(None, status=status.HTTP_404_NOT_FOUND)

    def transcript_to_dict(
        self, transcript: TranscriptModel
    ) -> dict[str, Any]:
        """Serialize a transcript model."""
        output: dict[str, Any] = {}
        output["transcript_id"] = transcript.tr_id
        output["strand"] = transcript.strand
        output["chrom"] = transcript.chrom
        output["cds"] = self.cds_to_dictlist(transcript.cds)
        output["utr3"] = []
        for region in transcript.utr3_regions():
            output["utr3"].append(self.region_to_dict(region))
        output["utr5"] = []
        for region in transcript.utr5_regions():
            output["utr5"].append(self.region_to_dict(region))
        output["exons"] = []
        for exon in transcript.exons:
            output["exons"].append(self.exon_to_dict(exon))
        return output

    def cds_to_dictlist(self, cds: tuple[int, int]) -> list[dict[str, Any]]:
        return [
            {"start": cds[0], "stop": cds[1]}
        ]

    def region_to_dict(self, region: Region) -> dict[str, Any]:
        return {
            "start": region.start,
            "stop": region.stop
        }

    def exon_to_dict(self, exon: Exon) -> dict[str, Any]:
        return {
            "start": exon.start,
            "stop": exon.stop
        }


class GeneSymbolsSearch(QueryBaseView):
    """Process search for a gene symbol."""

    RESPONSE_LIMIT = 20

    def get(self, _request: Request, search_term: str) -> Response:
        """Return list of gene symbols matching the search."""
        search_term = search_term.lower()
        gene_models = self.gpf_instance.gene_models.gene_models

        matching_gene_symbols = islice(
            filter(
                lambda gs: gs.lower().startswith(search_term),
                gene_models.keys()
            ),
            None,
            self.RESPONSE_LIMIT
        )

        return Response(
            {"gene_symbols": list(matching_gene_symbols)},
            status=status.HTTP_200_OK,
        )
