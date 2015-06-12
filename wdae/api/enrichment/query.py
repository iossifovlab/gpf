'''
Created on Jun 12, 2015

@author: lubo
'''
from query_prepare import prepare_denovo_studies, \
    prepare_string_value, combine_gene_syms
from api.enrichment.results import EnrichmentTestBuilder


def enrichment_prepare(data):
    result = {'denovoStudies': prepare_denovo_studies(data),
              'geneSet': prepare_string_value(data, 'geneSet'),
              'geneTerm': prepare_string_value(data, 'geneTerm'),
              'gene_set_phenotype': prepare_string_value(data, 'gene_set_phenotype'),
              'geneSyms': combine_gene_syms(data)}

    if 'geneSet' not in result or result['geneSet'] is None or \
       'geneTerm' not in result or result['geneTerm'] is None:
        del result['geneSet']
        del result['geneTerm']
        del result['gene_set_phenotype']

    if 'geneSet' in result and result['geneSet'] != 'denovo':
        del result['gene_set_phenotype']

    if not all(result.values()):
        return None

    return result



class Query(object):
    
    
    @classmethod
    def make_query(cls, request, background):
        query = enrichment_prepare(request)
        if not query:
            return None
        return Query(query, background)
    
    def __init__(self, query, background):
        self.query = query
        self.background = background
        
    def build(self):
        self.enrichment_test = EnrichmentTestBuilder()
        self.enrichment_test.build(self.background)
        
    def calc(self):
        dsts = self.query['denovoStudies']
        gene_syms = self.query['geneSyms']
        self.result = self.enrichment_test.calc(dsts, gene_syms)
        
        return self.result
    
        