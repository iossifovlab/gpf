from preloaded import register
from common.query_base import GeneSymsMixin
from datasets_api.permissions import IsDatasetAllowed


def expand_gene_set(request_function):
    def decorated(self, request):
        if 'geneSet' in request.data:
            gene_sets_collection_id, gene_set_id, gene_sets_types = \
                GeneSymsMixin.get_gene_set_query(**request.data)
            gene_sets_collections = register.get('gene_sets_collections')
            gene_set = gene_sets_collections.get_gene_set(
                gene_sets_collection_id, gene_set_id, gene_sets_types,
                IsDatasetAllowed.permitted_datasets(request.user))
            del request.data['geneSet']
            request.data['geneSymbols'] = gene_set['syms']
        return request_function(self, request)
    return decorated

