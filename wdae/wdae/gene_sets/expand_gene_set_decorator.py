from datasets_api.studies_manager import get_studies_manager

from dae.utils.query_base import GeneSymsMixin
from datasets_api.permissions import IsDatasetAllowed


def expand_gene_set(request_function):
    def decorated(self, request):
        if 'geneSet' in request.data:
            gene_sets_collection_id, gene_set_id, gene_sets_types = \
                GeneSymsMixin.get_gene_set_query(**request.data)
            if gene_sets_collection_id == 'denovo':
                dgsf = get_studies_manager().get_denovo_gene_set_facade()
                gene_set = dgsf.get_denovo_gene_set(
                    gene_sets_collection_id,
                    gene_set_id,
                    gene_sets_types,
                    IsDatasetAllowed.permitted_datasets(request.user)
                )
            else:
                gene_sets_collections =\
                    get_studies_manager().get_gene_sets_collections()
                gene_set = gene_sets_collections.get_gene_set(
                    gene_sets_collection_id, gene_set_id, gene_sets_types,
                    IsDatasetAllowed.permitted_datasets(request.user))
            # del request.data['geneSet']
            request.data['geneSymbols'] = gene_set['syms']
            request.data['geneSet'] = gene_set['desc']
        return request_function(self, request)
    return decorated
