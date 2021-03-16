import os
import logging

from typing import Dict, List, Optional

from dae.gene.utils import getGeneTerms, getGeneTermAtt, rename_gene_terms
from dae.gene.gene_term import loadGeneTerm
from dae.utils.dae_utils import cached

LOGGER = logging.getLogger(__name__)


class GeneSet:
    name: str
    desc: str
    count: int
    syms: List[str]

    def __init__(self, name: str, desc: str, syms: List[str]):
        self.name = name
        self.desc = desc
        self.count = len(syms)
        self.syms = syms

    def __getitem__(self, name):
        if name == "name":
            return self.name
        elif name == "desc":
            return self.desc
        elif name == "count":
            return self.count
        elif name == "syms":
            return self.syms
        else:
            raise KeyError()


class GeneSetCollection(object):
    collection_id: str
    gene_sets: Dict[str, GeneSet] = dict()

    def __init__(self, collection_id: str, gene_sets: List[GeneSet]):
        assert collection_id != "denovo"

        self.collection_id = collection_id
        for gene_set in gene_sets:
            self.gene_sets[gene_set.name] = gene_set

        assert self.collection_id, self.gene_sets

    @staticmethod
    def from_config(collection_id: str, config) -> "GeneSetCollection":
        gene_sets = list()
        gene_terms = getGeneTerms(config, collection_id, inNS="sym")
        for key, value in gene_terms.tDesc.items():
            syms = list(gene_terms.t2G[key].keys())
            gene_sets.append(GeneSet(key, value, syms))
        return GeneSetCollection(collection_id, gene_sets)

    def get_gene_set(self, gene_set_id: str) -> Optional[GeneSet]:
        gene_set = self.gene_sets.get(gene_set_id)
        if gene_set is None:
            print(f"{gene_set_id} not found in {self.gene_sets.keys()}")
        return gene_set


class GeneSetsDb(object):
    def __init__(self, config, load_eagerly=False):
        assert config is not None
        self.config = config
        self.gene_set_collections: Dict[str, GeneSetCollection] = dict()
        self.load_eagerly = load_eagerly
        if load_eagerly:
            LOGGER.info(
                f"GeneSetsDb created with load_eagerly={load_eagerly}")

            for collection_id in self.get_gene_set_collection_ids():
                LOGGER.debug(
                    f"loading gene set collection <{collection_id}>")
                self._load_gene_set_collection(collection_id)
            LOGGER.info(
                f"gene set collections <{self.get_gene_set_collection_ids()}> "
                f"loaded")

    @property  # type: ignore
    @cached
    def collections_descriptions(self):
        gene_sets_collections_desc = []
        if self.config.gene_terms:
            for gsc_id in self.config.gene_terms:
                label = getGeneTermAtt(self.config, gsc_id, "web_label")
                format_str = getGeneTermAtt(
                    self.config, gsc_id, "web_format_str"
                )
                if not label or not format_str:
                    continue
                gene_sets_collections_desc.append(
                    {
                        "desc": label,
                        "name": gsc_id,
                        "format": format_str.split("|"),
                        "types": [],
                    }
                )
        return gene_sets_collections_desc

    @staticmethod
    def load_gene_set_from_file(filename, config):
        assert os.path.exists(filename) and os.path.isfile(filename)
        gene_term = loadGeneTerm(filename)
        gene_term = rename_gene_terms(config, gene_term, inNS="sym")
        return gene_term

    def _load_gene_set_collection(self, gene_sets_collection_id):
        if gene_sets_collection_id not in self.gene_set_collections:
            LOGGER.info(
                f"gene set collection <{gene_sets_collection_id}> "
                f"not found in GeneSetDb cache")
            self.gene_set_collections[gene_sets_collection_id] = \
                GeneSetCollection.from_config(
                    gene_sets_collection_id, self.config
                )
            LOGGER.info(
                f"gene set collection <{gene_sets_collection_id}> "
                f"loaded into GeneSetsDb cache")
        return self.gene_set_collections[gene_sets_collection_id]

    def has_gene_set_collection(self, gsc_id):
        return any(
            [gsc["name"] == gsc_id for gsc in self.collections_descriptions]
        )

    def get_gene_set_collection_ids(self):
        """
        Return all gene set collection ids (including the ids
        of collections which have not been loaded).
        """
        return set(self.config.gene_terms)

    def get_gene_set_ids(self, collection_id):
        gsc = self._load_gene_set_collection(collection_id)
        return set(gsc.gene_sets.keys())

    def get_all_gene_sets(self, collection_id):
        gsc = self._load_gene_set_collection(collection_id)
        return list(gsc.gene_sets.values())

    def get_gene_set(self, collection_id, gene_set_id):
        gsc = self._load_gene_set_collection(collection_id)
        return gsc.get_gene_set(gene_set_id)
