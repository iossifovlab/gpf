"""Classes for handling of gene sets."""

import logging
from typing import Dict, List, Optional, cast, Set
from urllib.parse import urlparse
from functools import cached_property

from sqlalchemy import create_engine  # type: ignore
from sqlalchemy import MetaData, Table, Column, String
from sqlalchemy.sql import insert


from dae.genomic_resources.fsspec_protocol import FsspecReadOnlyProtocol
from dae.gene.gene_term import read_ewa_set_file, read_gmt_file, \
    read_mapping_file
from dae.genomic_resources.repository import GenomicResource

logger = logging.getLogger(__name__)


class GeneSet:
    """Class representing a set of genes."""

    # FIXME: consider using a dataclass
    # pylint: disable=too-few-public-methods
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
        if name == "desc":
            return self.desc
        if name == "count":
            return self.count
        if name == "syms":
            return self.syms

        raise KeyError()


class GeneSetCollection:
    """Class representing a collection of gene sets."""

    def __init__(
            self, collection_id: str, gene_sets: List[GeneSet],
            web_label: str = None, web_format_str: str = None):

        assert collection_id != "denovo"

        self.collection_id: str = collection_id
        self.gene_sets: Dict[str, GeneSet] = {}
        self.web_label = web_label
        self.web_format_str = web_format_str

        for gene_set in gene_sets:
            self.gene_sets[gene_set.name] = gene_set

        assert self.collection_id, self.gene_sets

    @staticmethod
    def from_resource(resource: GenomicResource):
        """Build a gene set collection from a given GenomicResource."""
        # pylint: disable=too-many-locals
        assert resource is not None
        gene_sets = []
        config = resource.get_config()
        collection_id = config["id"]
        assert resource.get_type() == "gene_set", "Invalid resource type"
        collection_format = config["format"]
        web_label = config.get("web_label", None)
        web_format_str = config.get("web_format_str", None)
        logger.debug("loading %s: %s", collection_id, config)

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
            filepaths = []
            if directory == ".":
                directory = ""  # Easier check with startswith
            for filepath, _ in resource.get_manifest().get_files():
                if filepath.startswith(directory) and \
                        filepath.endswith(".txt"):
                    filepaths.append(filepath)

            files = [resource.open_raw_file(f) for f in filepaths]

            gene_terms = read_ewa_set_file(files)
        elif collection_format == "sqlite":
            dbfile = config["dbfile"]
            if not isinstance(resource.proto, FsspecReadOnlyProtocol) and \
                    cast(FsspecReadOnlyProtocol,
                         resource.proto).scheme != "file":
                raise ValueError(
                    "sqlite gene sets are supported only on local filesystem")
            proto: FsspecReadOnlyProtocol = \
                cast(FsspecReadOnlyProtocol, resource.proto)
            dbfile_url = proto.get_resource_file_url(resource, dbfile)
            dbfile_path = urlparse(dbfile_url).path

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
        """Return the gene set if found; returns None if not found."""
        gene_set = self.gene_sets.get(gene_set_id)
        if gene_set is None:
            logger.warning(
                "%s not found in %s", gene_set_id, self.gene_sets.keys()
            )
        return gene_set

    def get_all_gene_sets(self) -> List[GeneSet]:
        return list(self.gene_sets.values())


class SqliteGeneSetCollectionDB:
    """Collection of gene sets stored in a SQLite database."""

    def __init__(
        self, collection_id: str, dbfile: str,
        web_label: str = None, web_format_str: str = None
    ):
        self.collection_id = collection_id
        self.web_label = web_label
        self.web_format_str = web_format_str
        self.dbfile = dbfile
        self.engine = create_engine(f"sqlite:///{dbfile}")
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

    def add_gene_set(self, gene_set: GeneSet):
        """Add a gene set to the database."""
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
        """Fetch and construct a GeneSet from the database."""
        table = self.gene_sets_table
        select = table.select().where(table.c.name == gene_set_id)
        with self.engine.connect() as connection:
            row = connection.execute(select).fetchone()
            gene_set = GeneSet(
                row["name"],
                row["desc"],
                row["syms"].split(",")
            )
            return gene_set


class GeneSetsDb:
    """Class that represents a dictionary of gene set collections."""

    def __init__(self, gene_set_collections):
        self.gene_set_collections: Dict[str, GeneSetCollection] = {
            gsc.collection_id: gsc
            for gsc in gene_set_collections
        }

    @cached_property
    def collections_descriptions(self):
        """Collect gene set descriptions.

        Iterates and creates a list of descriptions
        for each gene set collection
        """
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
        """Check the database if contains the specified gene set collection."""
        return gsc_id in self.gene_set_collections

    def get_gene_set_collection_ids(self) -> Set[str]:
        """Return all gene set collection ids.

        Including the ids of collections which have not been loaded.
        """
        return set(self.gene_set_collections.keys())

    def get_gene_set_ids(self, collection_id) -> Set[str]:
        """Return the IDs of all the gene sets in specified collection."""
        gsc = self.gene_set_collections[collection_id]
        return set(gsc.gene_sets.keys())

    def get_all_gene_sets(self, collection_id) -> List[GeneSet]:
        """Return all the gene sets in the specified collection."""
        gsc = self.gene_set_collections[collection_id]
        logger.debug(
            "gene sets from %s: %s", collection_id, len(gsc.gene_sets.keys()))
        return list(gsc.gene_sets.values())

    def get_gene_set(self, collection_id, gene_set_id) -> Optional[GeneSet]:
        """Find and return a gene set in a gene set collection."""
        gsc = self.gene_set_collections[collection_id]
        return gsc.get_gene_set(gene_set_id)

    def __len__(self):
        return len(self.gene_set_collections)
