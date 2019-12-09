from gpf_instance.gpf_instance import get_gpf_instance

from datasets_api.permissions import IsDatasetAllowed

from dae.utils.gene_utils import GeneSymsMixin


def expand_gene_set(request_function):
    def decorated(self, request):
        if 'geneSet' in request.data:
            gene_sets_collection_id, gene_set_id, gene_sets_types = \
                GeneSymsMixin.get_gene_set_query(**request.data)
            if gene_sets_collection_id == 'denovo':
                denovo_gene_sets_db = get_gpf_instance().denovo_gene_sets_db
                gene_set = denovo_gene_sets_db.get_gene_set(
                    gene_set_id,
                    gene_sets_types,
                    IsDatasetAllowed.permitted_datasets(request.user)
                )
            else:
                gene_sets_db = get_gpf_instance().gene_sets_db
                gene_set = gene_sets_db.get_gene_set(
                    gene_sets_collection_id, gene_set_id)
            # del request.data['geneSet']
            request.data['geneSymbols'] = gene_set['syms']
            request.data['geneSet'] = gene_set['desc']
        return request_function(self, request)
    return decorated
