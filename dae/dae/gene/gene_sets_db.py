import os
import logging

from dae.gene.gene_info_config import GeneInfoConfigParser, GeneInfoDB
from dae.gene.gene_term import loadGeneTerm

LOGGER = logging.getLogger(__name__)


class GeneSetsCollection(object):

    def __init__(self, gene_sets_collection_id, config):
        self.config = config

        assert gene_sets_collection_id != 'denovo'
        self.gsc_id = gene_sets_collection_id
        self.gene_sets_descriptions = None
        self.gene_sets_collections = None

    @staticmethod
    def _load_collection(config, gene_sets_collection):
        assert gene_sets_collection.geneNS in ['id', 'sym'], \
            'The namespace must be either "id" or "sym"!'

        if gene_sets_collection.geneNS == 'id':
            def rF(x):
                genes = GeneInfoDB.getGenes(config.gene_info)
                if x in genes:
                    return genes[x].sym
            gene_sets_collection.renameGenes('sym', rF)

        return gene_sets_collection

    def load(self, from_file=False):
        if self.gene_sets_collections:
            return self.gene_sets_collections

        if from_file:
            assert os.path.exists(self.gsc_id) and os.path.isfile(self.gsc_id)
            gsc = loadGeneTerm(self.gsc_id)
        else:
            gsc = GeneInfoConfigParser.getGeneTerms(self.config, self.gsc_id)

        self.gene_sets_collections = self._load_collection(self.config, gsc)

        self.gene_sets_descriptions = [
            {
                'name': key,
                'desc': value,
                'count': len(list(self.gene_sets_collections.t2G[key].keys()))
            }
            for key, value in list(self.gene_sets_collections.tDesc.items())
        ]
        return self.gene_sets_collections

    def get_gene_sets(self):
        assert self.gene_sets_collections is not None
        assert self.gene_sets_descriptions is not None
        return self.gene_sets_descriptions

    def get_gene_set(self, gene_set_id):
        assert self.gene_sets_collections is not None

        if gene_set_id not in self.gene_sets_collections.t2G:
            print("{} not found in {}".format(
                gene_set_id,
                self.gene_sets_collections.t2G.keys()))
            return None
        syms = set(self.gene_sets_collections.t2G[gene_set_id].keys())
        count = len(syms)
        desc = self.gene_sets_collections.tDesc[gene_set_id]

        return {
            "name": gene_set_id,
            "count": count,
            "syms": syms,
            "desc": desc,
        }


class GeneSetsDb(object):

    def __init__(self, variants_db, config):
        assert config is not None
        self.config = config

        self.variants_db = variants_db
        self.gene_sets_collections = {}

    def get_gene_set_collection_ids(self):
        return self.config.gene_terms.keys()

    def get_gene_set_ids(self, collection_id):
        gsc = self.get_gene_sets_collection(collection_id)
        if gsc is None:
            return None
        return gsc.gene_sets_collections.tDesc.keys()

    def get_collections_descriptions(self):
        gene_sets_collections_desc = []
        for gsc_id in self.config.gene_terms.keys():
            label = GeneInfoConfigParser.getGeneTermAtt(
                self.config, gsc_id, "webLabel")
            formatStr = GeneInfoConfigParser.getGeneTermAtt(
                self.config, gsc_id, "webFormatStr")
            if not label or not formatStr:
                continue
            gene_sets_collections_desc.append(
                {
                    'desc': label,
                    'name': gsc_id,
                    'format': formatStr.split("|"),
                    'types': [],
                }
            )
        return gene_sets_collections_desc

    def has_gene_sets_collection(self, gsc_id):
        return any([
            gsc['name'] == gsc_id
            for gsc in self.get_collections_descriptions()
        ])

    @staticmethod
    def load_gene_set_from_file(filename, config):
        assert os.path.exists(filename) and os.path.isfile(filename)
        return GeneSetsCollection._load_collection(
            config,
            loadGeneTerm(filename)
        )

    def _load_gene_set(self, gene_sets_collection_id, load=True):
        gsc = GeneSetsCollection(gene_sets_collection_id, config=self.config)

        if load:
            gsc.load()

        return gsc

    def get_gene_sets_collection(self, gene_sets_collection_id, load=True):
        assert gene_sets_collection_id != 'denovo'

        if gene_sets_collection_id not in self.gene_sets_collections:
            gsc = self._load_gene_set(gene_sets_collection_id, load)
            self.gene_sets_collections[gene_sets_collection_id] = gsc

        return self.gene_sets_collections.get(gene_sets_collection_id, None)

    def get_gene_sets(self, gene_sets_collection_id, load=True):
        assert gene_sets_collection_id != 'denovo'

        gsc = self.get_gene_sets_collection(gene_sets_collection_id, load)

        if gsc is None:
            return None

        return gsc.get_gene_sets()

    def get_gene_set(self, gene_sets_collection_id, gene_set_id):
        assert gene_sets_collection_id != 'denovo'

        gsc = self.get_gene_sets_collection(gene_sets_collection_id)

        if gsc is None:
            return None

        return gsc.get_gene_set(gene_set_id)
