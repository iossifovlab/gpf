import os
import logging

from dae.gene.gene_info_config import GeneInfoConfigParser
from dae.gene.gene_term import loadGeneTerm

LOGGER = logging.getLogger(__name__)


def cached(prop):
    # FIXME This has been duplicated temporarily - once
    # the master branch is merged into this branch, this
    # should be removed

    cached_val_name = '_' + prop.__name__

    def wrap(self):
        if getattr(self, cached_val_name, None) is None:
            setattr(self, cached_val_name, prop(self))
        return getattr(self, cached_val_name)

    return wrap


class GeneSetCollection(object):

    def __init__(self, gene_sets_collection_id, config):
        assert gene_sets_collection_id != 'denovo'

        self.gsc_id = gene_sets_collection_id

        self.gene_terms = GeneInfoConfigParser.getGeneTerms(
            config, self.gsc_id, inNS='sym'
        )
        assert self.gene_terms, self.gsc_id

        self.gene_terms_descriptions = dict()
        for key, value in self.gene_terms.tDesc.items():
            syms = list(self.gene_terms.t2G[key].keys())
            self.gene_terms_descriptions[key] = {
                'name': key,
                'desc': value,
                'count': len(syms),
                'syms': syms,
            }
        assert self.gene_terms_descriptions, self.gsc_id

    def get_gene_set(self, gene_set_id):
        if gene_set_id not in self.gene_terms_descriptions:
            print(f'{gene_set_id} not found in '
                  '{self.gene_terms_descriptions.keys()}')
            return None
        return self.gene_terms_descriptions[gene_set_id]


class GeneSetsDb(object):

    def __init__(self, config):
        assert config is not None
        self.config = config
        self.gene_set_collections = dict()

    @property
    @cached
    def collections_descriptions(self):
        gene_sets_collections_desc = []
        for gsc_id in self.config.gene_terms.keys():
            label = GeneInfoConfigParser.getGeneTermAtt(
                self.config, gsc_id, 'webLabel')
            formatStr = GeneInfoConfigParser.getGeneTermAtt(
                self.config, gsc_id, 'webFormatStr')
            if not label or not formatStr:
                continue
            gene_sets_collections_desc.append(
                {
                    'desc': label,
                    'name': gsc_id,
                    'format': formatStr.split('|'),
                    'types': [],
                }
            )
        return gene_sets_collections_desc

    @staticmethod
    def load_gene_set_from_file(filename, config):
        assert os.path.exists(filename) and os.path.isfile(filename)
        gene_term = loadGeneTerm(filename)
        gene_term = GeneInfoConfigParser._rename_gene_terms(
            config, gene_term, inNS='sym'
        )
        return gene_term

    def _load_gene_set_collection(self, gene_sets_collection_id):
        if gene_sets_collection_id not in self.gene_set_collections:
            self.gene_set_collections[gene_sets_collection_id] = \
                GeneSetCollection(gene_sets_collection_id, config=self.config)
        return self.gene_set_collections[gene_sets_collection_id]

    def has_gene_set_collection(self, gsc_id):
        return any([
            gsc['name'] == gsc_id
            for gsc in self.collections_descriptions
        ])

    def get_gene_set_collection_ids(self):
        '''
        Return all gene set collection ids (including the ids
        of collections which have not been loaded).
        '''
        return self.config.gene_terms.keys()

    def get_gene_set_ids(self, collection_id):
        gsc = self._load_gene_set_collection(collection_id)
        return set(gsc.gene_terms_descriptions.keys())

    def get_all_gene_sets(self, collection_id):
        gsc = self._load_gene_set_collection(collection_id)
        return list(gsc.gene_terms_descriptions.values())

    def get_gene_set(self, collection_id, gene_set_id):
        gsc = self._load_gene_set_collection(collection_id)
        return gsc.get_gene_set(gene_set_id)
