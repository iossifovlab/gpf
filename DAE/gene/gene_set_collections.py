'''
Created on Feb 16, 2017

@author: lubo
'''
from gene.config import GeneInfoConfig
import sqlite3
from DAE import giDB, get_gene_sets_symNS
from denovo_gene_sets import build_denovo_gene_sets


class CacheMixin(object):
    pass


class GeneSetsCollection(object):

    def __init__(self, gene_sets_collection_id):
        assert gene_sets_collection_id != 'denovo'
        self.gsc_id = gene_sets_collection_id
        self.gene_sets_descriptions = None

    def load(self):
        self.gene_sets_collection = get_gene_sets_symNS(self.gsc_id)
        self.gene_sets_descriptions = [
            {
                'name': key,
                'desc': value,
                'count': len(self.gene_sets_collection.t2G[key].keys())
            }
            for key, value in self.gene_sets_collection.tDesc.items()
        ]
        return self.gene_sets_collection

    def get_gene_sets(self, gene_sets_types=[], **kwargs):
        assert self.gene_sets_collection is not None
        assert self.gene_sets_descriptions is not None
        return self.gene_sets_descriptions

    def get_gene_sets_types(self):
        return []

    def get_gene_set(self, gene_set_id, gene_sets_types=[], **kwargs):
        assert self.gene_set_collection is not None

        if gene_set_id not in self.gene_set_collection.t2G:
            return None
        syms = self.gene_set_collection.t2G[gene_set_id].keys()
        count = len(syms)
        desc = self.gene_set_collection.tDesc[gene_set_id]

        return {
            "name": gene_set_id,
            "count": count,
            "syms": syms,
            "desc": desc,
        }


class DenovoGeneSetsType(object):

    def __init__(self, gene_term):
        self.gene_term = gene_term

    def get_gene_set_syms(self, gene_set_id, **kwargs):
        assert self.gene_term is not None

        if gene_set_id not in self.gene_term.t2G:
            print("gene set {} not found...".format(gene_set_id))
            return set()
        syms = self.gene_term.t2G[gene_set_id].keys()
        return set(syms)

    def get_gene_sets(self):
        keys = self.gene_term.tDesc.keys()[:]
        keys = sorted(keys)
        return keys


class DenovoGeneSetsCollection(object):
    GENE_SETS_TYPES = [
        'autism',
        'congenital heart disease',
        'epilepsy',
        'intelectual disability',
        'schizophrenia',
        'unaffected'
    ]

    def __init__(self):
        self.gene_sets_types = self.GENE_SETS_TYPES
        self.gene_sets_collection_desc = None
        self.gene_sets_names = None

    def load(self):
        computed = build_denovo_gene_sets()
        self.gene_sets_collection = {}
        for gene_sets_type, gene_term in computed.items():
            self.gene_sets_collection[gene_sets_type] = \
                DenovoGeneSetsType(gene_term)
        self.gene_sets_collection_desc = {}

        self.gene_sets_names = \
            self.gene_sets_collection[self.gene_sets_types[0]].get_gene_sets()
        return self.gene_sets_collection

    def get_gene_sets_types(self):
        return self.gene_sets_types

    def get_gene_sets(self, gene_sets_types=[], **kwargs):
        gene_sets_types = [
            gst for gst in gene_sets_types
            if gst in self.gene_sets_types
        ]

        if gene_sets_types == []:
            gene_sets_types = ['autism']

        gene_sets_types_desc = ','.join(gene_sets_types)
        result = []
        for gsn in self.gene_sets_names:
            gene_set_syms = self._get_gene_set_syms(gsn, gene_sets_types)
            result.append({
                'name': gsn,
                'count': len(gene_set_syms),
                'syms': gene_set_syms,
                'desc': '{} ({})'.format(gsn, gene_sets_types_desc)
            })
        return result

    def _get_gene_set_syms(self, gene_set_name, gene_sets_types):
        result = [
            self.gene_sets_collection[gst].get_gene_set_syms(gene_set_name)
            for gst in gene_sets_types
        ]

        syms = reduce(
            lambda s1, s2: s1 | s2,
            result)
        return syms

    def get_gene_set(self, gene_set_id, gene_sets_types=[], **kwargs):
        gene_sets_types = [
            gst for gst in gene_sets_types
            if gst in self.gene_sets_types
        ]

        if gene_sets_types == []:
            gene_sets_types = ['autism']
        syms = self._get_gene_set_syms(gene_set_id, gene_sets_types)

        return {
            "name": gene_set_id,
            "count": len(syms),
            "syms": syms,
            "desc": "{} ({})".format(gene_set_id, ";".join(gene_sets_types)),
        }


class GeneSetsCollections(GeneInfoConfig):

    def __init__(self):
        super(GeneSetsCollections, self).__init__()

        self.cache = self.config.get("cache", "file")
        self.db = None
        self.gene_sets_collections = {}
        self.gene_sets_collections_desc = None

    def connect(self):
        if self.db is not None:
            return self.db
        self.db = sqlite3.connect(self.cache, isolation_level="DEFERRED")
        return self.db

    def is_connected(self):
        return self.db is not None

    def get_gene_sets_collections(self):
        if self.gene_sets_collections_desc:
            return self.gene_sets_collections_desc

        self.gene_sets_collections_desc = []
        for gsc_id in giDB.getGeneTermIds():
            label = giDB.getGeneTermAtt(gsc_id, "webLabel")
            formatStr = giDB.getGeneTermAtt(gsc_id, "webFormatStr")
            if not label or not formatStr:
                continue
            gene_sets_types = []
            if gsc_id == 'denovo':
                gene_sets_types = DenovoGeneSetsCollection.GENE_SETS_TYPES

            self.gene_sets_collections_desc.append(
                {
                    'desc': label,
                    'name': gsc_id,
                    'format': formatStr.split("|"),
                    'types': gene_sets_types,
                }
            )

        return self.gene_sets_collections_desc

    def has_gene_sets_collection(self, gsc_id):
        print(self.get_gene_sets_collections())
        print([
            gsc['name'] == gsc_id
            for gsc in self.get_gene_sets_collections()
        ])
        return any([
            gsc['name'] == gsc_id
            for gsc in self.get_gene_sets_collections()
        ])

    def get_gene_sets_collection(self, gene_sets_collection_id):
        if gene_sets_collection_id not in self.gene_sets_collections:
            if gene_sets_collection_id == 'denovo':
                gsc = DenovoGeneSetsCollection()
            else:
                gsc = GeneSetsCollection(gene_sets_collection_id)
            if gsc.load():
                self.gene_sets_collections[gene_sets_collection_id] = gsc
        return self.gene_sets_collections.get(gene_sets_collection_id, None)

    def get_gene_sets(self, gene_sets_collection_id, gene_sets_types=[]):
        gsc = self.get_gene_sets_collection(gene_sets_collection_id)
        if gsc is None:
            return None

        return gsc.get_gene_sets(gene_sets_types)

    def get_gene_set(
            self, gene_sets_collection_id, gene_set_id, gene_sets_types=[]):
        gsc = self.get_gene_sets_collection(gene_sets_collection_id)
        if gsc is None:
            return None
        return gsc.get_gene_set(gene_set_id, gene_sets_types)
