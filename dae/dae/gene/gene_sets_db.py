import logging
from sqlalchemy import create_engine  # type: ignore
from sqlalchemy import MetaData, Table, Column, String
from sqlalchemy.sql import insert

from typing import Dict, List, Optional, Any

from dae.gene.gene_term import read_ewa_set_file, read_gmt_file, \
    read_mapping_file
from dae.genomic_resources.repository import GenomicResource
from dae.utils.dae_utils import cached

logger = logging.getLogger(__name__)


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
        # This is done so that GeneSet instances and
        # denovo gene set dictionaries can be accessed in a uniform way
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


class GeneSetCollection:

    def __init__(
            self, collection_id: str, gene_sets: List[GeneSet],
            web_label: str = None, web_format_str: str = None):

        assert collection_id != "denovo"

        self.collection_id: str = collection_id
        self.gene_sets: Dict[str, GeneSet] = dict()
        self.web_label = web_label
        self.web_format_str = web_format_str

        for gene_set in gene_sets:
            self.gene_sets[gene_set.name] = gene_set

        assert self.collection_id, self.gene_sets

    @staticmethod
    def from_resource(resource: GenomicResource):
        assert resource is not None
        gene_sets = list()
        config = resource.get_config()
        collection_id = config["id"]
        assert resource.get_type() == "gene_set", "Invalid resource type"
        collection_format = config["format"]
        web_label = config.get("web_label", None)
        web_format_str = config.get("web_format_str", None)
        logger.debug(f"loading {collection_id}: {config}")

        if collection_format == "map":
            filename = config["filename"]
            names_filename = filename[:-4] + "names.txt"
            names_file = None
            if resource.file_exists(names_filename):
                names_file = resource.open_raw_file(names_filename)
            gene_terms = read_mapping_file(
                resource.open_raw_file(filename),
                names_file
            )
        elif collection_format == "gmt":
            filename = config["filename"]
            gene_terms = read_gmt_file(resource.open_raw_file(filename))
        elif collection_format == "directory":
            directory = config["directory"]
            filepaths = list()
            if directory == ".":
                directory = ""  # Easier check with startswith
            for filepath, _, _ in resource.get_files():
                if filepath.startswith(directory) and \
                        filepath.endswith(".txt"):
                    filepaths.append(filepath)

            files = [resource.open_raw_file(f) for f in filepaths]

            gene_terms = read_ewa_set_file(files)
        elif collection_format == "sqlite":
            dbfile = config["dbfile"]
            assert resource.file_local(dbfile)
            dbfile_path = resource.repo.get_file_path(resource, dbfile)
            return SqliteGeneSetCollectionDB(
                collection_id,
                dbfile_path,
                web_label,
                web_format_str
            )
        else:
            raise ValueError("Invalid collection format type")

        for key, value in gene_terms.tDesc.items():
            syms = list(gene_terms.t2G[key].keys())
            gene_sets.append(GeneSet(key, value, syms))

        return GeneSetCollection(
            collection_id, gene_sets,
            web_label=web_label, web_format_str=web_format_str
        )

    def get_gene_set(self, gene_set_id: str) -> Optional[GeneSet]:
        gene_set = self.gene_sets.get(gene_set_id)
        if gene_set is None:
            print(f"{gene_set_id} not found in {self.gene_sets.keys()}")
        return gene_set


class SqliteGeneSetCollectionDB:
    def __init__(
        self, collection_id: str, dbfile: str,
        web_label: str = None, web_format_str: str = None
    ):
        self.collection_id = collection_id
        self.web_label = web_label
        self.web_format_str = web_format_str
        self.dbfile = dbfile
        self.engine = create_engine("sqlite:///{}".format(dbfile))
        self.metadata = MetaData(self.engine)
        self._create_gene_sets_table()

    def _create_gene_sets_table(self):
        self.gene_sets_table = Table(
            "gene_sets",
            self.metadata,
            Column("name", String(), primary_key=True),
            Column("desc", String()),
            Column("syms", String()),
        )

        self.metadata.create_all()

    def add_gene_set(self, gene_set):
        with self.engine.connect() as connection:
            insert_values = {
                "name": gene_set.name,
                "desc": gene_set.desc,
                "syms": ",".join(gene_set.syms)
            }
            connection.execute(
                insert(self.gene_sets_table).values(insert_values)
            )

    def get_gene_set(self, gene_set_id):
        table = self.gene_sets_table
        s = table.select().where(table.c.name == gene_set_id)
        with self.engine.connect() as connection:
            row = connection.execute(s).fetchone()
            gene_set = GeneSet(
                row["name"],
                row["desc"],
                row["syms"].split(",")
            )
            return gene_set


class GeneSetsDb(object):
    def __init__(self, gene_set_collections):
        self.gene_set_collections: Dict[str, GeneSetCollection] = {
            gsc.collection_id: gsc
            for gsc in gene_set_collections
        }

    @property  # type: ignore
    @cached
    def collections_descriptions(self):
        gene_sets_collections_desc = []
        for gsc in self.gene_set_collections.values():
            label = gsc.web_label
            format_str = gsc.web_format_str
            gsc_id = gsc.collection_id
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

    def has_gene_set_collection(self, gsc_id):
        return any(
            [gsc["name"] == gsc_id for gsc in self.collections_descriptions]
        )

    def get_gene_set_collection_ids(self):
        """
        Return all gene set collection ids (including the ids
        of collections which have not been loaded).
        """
        return set(self.gene_set_collections.keys())

    def get_gene_set_ids(self, collection_id):
        gsc = self.gene_set_collections[collection_id]
        return set(gsc.gene_sets.keys())

    def get_all_gene_sets(self, collection_id):
        gsc = self.gene_set_collections[collection_id]
        logger.debug(
            f"gene sets from {collection_id}: {len(gsc.gene_sets.keys())}")
        return list(gsc.gene_sets.values())

    def get_gene_set(self, collection_id, gene_set_id):
        gsc = self.gene_set_collections[collection_id]
        return gsc.get_gene_set(gene_set_id)
