import logging
import os

from datasets_api.permissions import get_instance_timestamp_etag
from django.utils.decorators import method_decorator
from django.views.decorators.http import etag
from query_base.query_base import QueryBaseView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class ConfigurationView(QueryBaseView):
    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, _request: Request) -> Response:
        configuration = self.gpf_instance.get_wdae_gp_configuration()
        if configuration is None:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(configuration)


class ProfileView(QueryBaseView):
    """Gene profiles single gene view."""

    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, _request: Request, gene_symbol: str) -> Response:
        """Get gene statistic and links to other information about the gene."""
        gp = self.gpf_instance.get_gp_statistic(gene_symbol)
        if not gp:
            return Response(status=status.HTTP_404_NOT_FOUND)
        result = gp.to_json()

        gp_config = self.gpf_instance \
            .get_wdae_gp_configuration()

        if isinstance(gp_config, dict):
            gene_link_templates = gp_config.get("geneLinks")
            if gene_link_templates:
                gene_symbol, transcript_models = \
                    self.gpf_instance.get_transcript_models(gene_symbol)
                if not transcript_models:
                    return Response(status=status.HTTP_404_NOT_FOUND)
                gpf_prefix = os.environ.get("WDAE_PREFIX", "")
                chromosome = transcript_models[0].chrom
                gene_start_position = transcript_models[0].exons[0].start
                gene_stop_position = transcript_models[-1].exons[-1].stop

                data_config = self.gpf_instance.get_genotype_data_config(
                    gp_config["defaultDataset"],
                )
                genome = None
                if data_config is not None:
                    genome = data_config.genome

                chromosome_prefix = "" if genome == "hg38" else "chr"

                gene_links = []
                for template in gene_link_templates:
                    gene_links.append({
                        "name": template["name"],
                        "url": template["url"].format(
                            gpf_prefix=gpf_prefix,
                            gene=gene_symbol,
                            genome=genome,
                            chromosome_prefix=chromosome_prefix,
                            chromosome=chromosome,
                            gene_start_position=gene_start_position,
                            gene_stop_position=gene_stop_position,
                        ),
                    })
                result["geneLinks"] = gene_links
        return Response(result)
