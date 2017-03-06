'''
Created on Feb 16, 2017

@author: lubo
'''
import os
from gene.config import GeneInfoConfig
import sqlite3
# from denovo_gene_sets import build_denovo_gene_sets
from GeneTerms import loadGeneTerm, GeneTerms
import traceback
from DAE import vDB
from itertools import groupby
from ipykernel.serialize import cPickle


class CacheMixin(object):
    pass


class GeneSetsCollection(GeneInfoConfig):

    def __init__(self, gene_sets_collection_id):
        super(GeneSetsCollection, self).__init__()

        assert gene_sets_collection_id != 'denovo'
        self.gsc_id = gene_sets_collection_id
        self.gene_sets_descriptions = None
        self.gene_sets_collections = None

    def _load(self):
        try:
            gene_sets_collection = self.gene_info.getGeneTerms(self.gsc_id)
        except:
            traceback.print_exc()
            gene_sets_collection = loadGeneTerm(self.gsc_id)

        if gene_sets_collection.geneNS == 'id':
            def rF(x):
                if x in self.gene_info.genes:
                    return self.gene_info.genes[x].sym
            gene_sets_collection.renameGenes("sym", rF)

        if gene_sets_collection.geneNS != 'sym':
            raise Exception('Only work with id or sym namespace')
        return gene_sets_collection

    def load(self):
        if self.gene_sets_collections:
            return self.gene_sets_collections

        self.gene_sets_collections = self._load()

        self.gene_sets_descriptions = [
            {
                'name': key,
                'desc': value,
                'count': len(self.gene_sets_collections.t2G[key].keys())
            }
            for key, value in self.gene_sets_collections.tDesc.items()
        ]
        return self.gene_sets_collections

    def get_gene_sets(self, gene_sets_types=[], **kwargs):
        assert self.gene_sets_collections is not None
        assert self.gene_sets_descriptions is not None
        return self.gene_sets_descriptions

    def get_gene_sets_types(self):
        return []

    def get_gene_sets_types_legend(self):
        return []

    def get_gene_set(self, gene_set_id, gene_sets_types=[], **kwargs):
        assert self.gene_sets_collections is not None

        if gene_set_id not in self.gene_sets_collections.t2G:
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


class DenovoGeneSetsCollection(GeneInfoConfig):
    GENE_SETS_TYPES = [
        'autism',
        'congenital heart disease',
        'epilepsy',
        'intelectual disability',
        'schizophrenia',
        'unaffected'
    ]
    GENE_SETS_TYPES_LEGEND = {
        "autism": {
            "color": "#e35252 ",
            "id": "autism",
            "name": "autism"
        },
        "congenital heart disease": {
            "color": "#b8008a ",
            "id": "congenital heart disease",
            "name": "congenital heart disease"
        },
        "epilepsy": {
            "color": "#e3d252 ",
            "id": "epilepsy",
            "name": "epilepsy"
        },
        "intelectual disability": {
            "color": "#99d8e8 ",
            "id": "intelectual disability",
            "name": "intelectual disability"
        },
        "schizophrenia": {
            "color": "#98e352 ",
            "id": "schizophrenia",
            "name": "schizophrenia"
        },
        "unaffected": {
            "color": "#ffffff ",
            "id": "unaffected",
            "name": "unaffected"
        },
    }
    DENOVO_STUDIES_COLLECTION = "ALL WHOLE EXOME"

    def __init__(self):
        super(DenovoGeneSetsCollection, self).__init__()

        self.gene_sets_types = self.GENE_SETS_TYPES
        self.gene_sets_collection_desc = None
        self.gene_sets_names = None

    def load_cache(self):
        cachename = self.config.get('cache', 'file')
        if not os.path.exists(cachename):
            return None

        with open(cachename, 'r') as infile:
            result = cPickle.load(infile)
            print(result)
            return result

    def save_cache(self, computed):
        cachename = self.config.get('cache', 'file')
        os.makedirs(os.path.dirname(cachename), exist_ok=True)
        with open(cachename, 'w') as outfile:
            cPickle.dump(computed, outfile)

    def load(self):
        computed = self.load_cache()
        if computed is None:
            computed = self.build_denovo_gene_sets()
            self.save_cache(computed)

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

    def get_gene_sets_types_legend(self):
        result = [
            self.GENE_SETS_TYPES_LEGEND[gt]
            for gt in self.get_gene_sets_types()
        ]
        return result

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

    @staticmethod
    def genes_sets(denovo_studies,
                   in_child=None,
                   effect_types=None,
                   gene_syms=None,
                   measure=None,
                   mmax=None,
                   mmin=None):

        vs = vDB.get_denovo_variants(denovo_studies,
                                     effectTypes=effect_types,
                                     inChild=in_child,
                                     geneSyms=gene_syms)

        if not (mmin or mmax):
            return {ge['sym'] for v in vs for ge in v.requestedGeneEffects}
        if mmin and measure:
            return {ge['sym']
                    for v in vs for ge in v.requestedGeneEffects
                    if measure.get(v.familyId, -1000) >= mmin}
        if mmax and measure:
            return {ge['sym']
                    for v in vs for ge in v.requestedGeneEffects
                    if measure.get(v.familyId, 1000) < mmax}
        return None

    @staticmethod
    def genes_set_prepare_counting(
            denovo_studies,
            in_child=None,
            effect_types=None,
            gene_set=None):

        vs = vDB.get_denovo_variants(denovo_studies,
                                     effectTypes=effect_types,
                                     inChild=in_child,
                                     geneSyms=gene_set)
        gnSorted = sorted([[ge['sym'], v]
                           for v in vs for ge in v.requestedGeneEffects])
        sym2Vars = {sym: [t[1] for t in tpi]
                    for sym, tpi in groupby(gnSorted, key=lambda x: x[0])}
        sym2FN = {sym: len(set([v.familyId for v in vs]))
                  for sym, vs in sym2Vars.items()}
        return sym2FN

    @staticmethod
    def genes_set_recurrent(
            denovo_studies,
            in_child=None,
            effect_types=None,
            gene_set=None):

        sym2FN = DenovoGeneSetsCollection.genes_set_prepare_counting(
            denovo_studies, in_child,
            effect_types, gene_set)
        return {g for g, nf in sym2FN.items() if nf > 1}

    @staticmethod
    def genes_set_single(
            denovo_studies,
            in_child=None,
            effect_types=None,
            gene_set=None):

        sym2FN = DenovoGeneSetsCollection.genes_set_prepare_counting(
            denovo_studies, in_child,
            effect_types, gene_set)
        return {g for g, nf in sym2FN.items() if nf == 1}

    def sib_sets(self, studies):
        res = {
            "LGDs": self.genes_sets(
                studies,
                in_child='sib',
                effect_types='LGDs'),
            "LGDs.Recurrent": self.genes_set_recurrent(
                studies,
                in_child="sib",
                effect_types="LGDs"),
            "LGDs.WE.Recurrent": self.genes_set_recurrent(
                [st for st in studies
                 if st.get_attr('study.type') == 'WE'],
                in_child="sib",
                effect_types="LGDs"),
            "Missense.Recurrent": self.genes_set_recurrent(
                studies,
                in_child='sib',
                effect_types='missense'),
            "Missense.WE.Recurrent": self.genes_set_recurrent(
                [st for st in studies
                 if st.get_attr('study.type') == 'WE'],
                in_child="sib",
                effect_types="missense"),
            "Missense": self.genes_sets(
                studies,
                in_child='sib',
                effect_types='missense'),
            "Synonymous": self.genes_sets(
                studies,
                in_child='sib',
                effect_types='synonymous'),
            "Synonymous.Recurrent": self.genes_set_recurrent(
                studies,
                in_child='sib',
                effect_types='synonymous'),
            "Synonymous.WE.Recurrent": self.genes_set_recurrent(
                [st for st in studies
                 if st.get_attr('study.type') == 'WE'],
                in_child="sib",
                effect_types="synonymous"),
            "CNV": self.genes_sets(
                studies,
                in_child='sib',
                effect_types='CNVs'),
            "Dup": self.genes_sets(
                studies,
                in_child='sib',
                effect_types='CNV+'),
            "Del": self.genes_sets(
                studies,
                in_child='sib',
                effect_types='CNV-'),
        }
        return res

    def get_measure(self, measure_id):
        from pheno.pheno_factory import PhenoFactory
        pf = PhenoFactory()
        pheno_db = pf.get_pheno_db('ssc')
        assert pheno_db is not None

        nvIQ = pheno_db.get_measure_values(measure_id)
        assert nvIQ is not None

        res = {}
        for person_id, value in nvIQ.items():
            family_id = person_id.split('.')[0]
            res[family_id] = value
        return res

    def prb_set(self, studies):
        nvIQ = self.get_measure('pheno_common.non_verbal_iq')

        res = {
            "LGDs": self.genes_sets(
                studies,
                in_child='prb',
                effect_types='LGDs'),

            "LGDs.Male": self.genes_sets(
                studies,
                in_child='prbM',
                effect_types='LGDs'),

            "LGDs.Female": self.genes_sets(
                studies,
                in_child='prbF',
                effect_types='LGDs'),

            "LGDs.Recurrent": self.genes_set_recurrent(
                studies,
                in_child="prb",
                effect_types="LGDs"),

            "LGDs.WE.Recurrent": self.genes_set_recurrent(
                [st for st in studies
                 if st.get_attr('study.type') == 'WE'],
                in_child="prb",
                effect_types="LGDs"),

            "LGDs.Single": self.genes_set_single(
                studies,
                in_child="prb",
                effect_types="LGDs"),

            "LGDs.LowIQ": self.genes_sets(
                studies,
                in_child='prb',
                effect_types='LGDs',
                measure=nvIQ,
                mmax=90),

            "LGDs.HighIQ": self.genes_sets(
                studies,
                in_child='prb',
                effect_types='LGDs',
                measure=nvIQ,
                mmin=90),

            #             "LGDs.FMRP": self.genes_sets(
            #                 studies,
            #                 in_child='prb',
            #                 effect_types='LGDs',
            #                 gene_syms=set_genes("main:FMR1-targets")),

            "Missense.Recurrent": self.genes_set_recurrent(
                studies,
                in_child="prb",
                effect_types="missense"),

            "Missense.WE.Recurrent": self.genes_set_recurrent(
                [st for st in studies
                 if st.get_attr('study.type') == 'WE'],
                in_child="prb",
                effect_types="missense"),

            "Missense": self.genes_sets(
                studies,
                in_child="prb",
                effect_types="missense"),
            "Missense.Male": self.genes_sets(
                studies,
                in_child="prbM",
                effect_types="missense"),
            "Missense.Female": self.genes_sets(
                studies,
                in_child="prbF",
                effect_types="missense"),
            "Synonymous.Recurrent": self.genes_set_recurrent(
                studies,
                in_child="prb",
                effect_types="synonymous"),

            "Synonymous.WE.Recurrent": self.genes_set_recurrent(
                [st for st in studies
                 if st.get_attr('study.type') == 'WE'],
                in_child="prb",
                effect_types="synonymous"),
            "Synonymous": self.genes_sets(
                studies,
                in_child="prb",
                effect_types="synonymous"),
            "CNV": self.genes_sets(
                studies,
                in_child="prb",
                effect_types="CNVs"),
            "CNV.Recurrent": self.genes_set_recurrent(
                studies,
                in_child="prb",
                effect_types="CNVs"),
            "Dup": self.genes_sets(
                studies,
                in_child="prb",
                effect_types="CNV+"),
            "Del": self.genes_sets(
                studies,
                in_child="prb",
                effect_types="CNV-"),
        }
        return res

    @staticmethod
    def add_set(gene_terms, setname, genes, desc=None):
        if not genes:
            return
        if desc:
            gene_terms.tDesc[setname] = desc
        else:
            gene_terms.tDesc[setname] = ''
        for gsym in genes:
            gene_terms.t2G[setname][gsym] += 1
            gene_terms.g2T[gsym][setname] += 1

    def build_denovo_gene_sets(self):
        denovo_studies = vDB.get_studies(self.DENOVO_STUDIES_COLLECTION)
        denovo_studies = denovo_studies[:]
        result = {}
        for phenotype in self.GENE_SETS_TYPES[:-1]:
            gene_terms = GeneTerms()
            studies = [
                st for st in denovo_studies
                if st.get_attr('study.phenotype') == phenotype
            ]
            res = self.prb_set(studies)
            for gene_set_name, gene_set in res.items():
                self.add_set(gene_terms, gene_set_name, gene_set)
            result[phenotype] = gene_terms
        gene_terms = GeneTerms()
        res = self.sib_sets(denovo_studies)
        for gene_set_name, gene_set in res.items():
            self.add_set(gene_terms, gene_set_name, gene_set)
        result['unaffected'] = gene_terms
        return result


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
        for gsc_id in self.gene_info.getGeneTermIds():
            label = self.gene_info.getGeneTermAtt(gsc_id, "webLabel")
            formatStr = self.gene_info.getGeneTermAtt(gsc_id, "webFormatStr")
            if not label or not formatStr:
                continue
            gene_sets_types = []
            if gsc_id == 'denovo':
                gene_sets_types = [
                    DenovoGeneSetsCollection.GENE_SETS_TYPES_LEGEND[gt]
                    for gt in DenovoGeneSetsCollection.GENE_SETS_TYPES
                ]
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
