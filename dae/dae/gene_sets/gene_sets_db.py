"""Classes for handling of gene sets."""

import abc
import copy
import logging
import os
import textwrap
from functools import cached_property
from typing import Any, Optional

from jinja2 import Template
from markdown2 import markdown

from dae.gene_sets.gene_term import (
    read_ewa_set_file,
    read_gmt_file,
    read_mapping_file,
)
from dae.genomic_resources.fsspec_protocol import build_local_resource
from dae.genomic_resources.repository import GenomicResource
from dae.genomic_resources.resource_implementation import (
    GenomicResourceImplementation,
    InfoImplementationMixin,
    ResourceConfigValidationMixin,
    get_base_resource_schema,
)
from dae.task_graph.graph import Task, TaskGraph

logger = logging.getLogger(__name__)


class GeneSet:
    """Class representing a set of genes."""

    # FIXME: consider using a dataclass
    # pylint: disable=too-few-public-methods
    name: str
    desc: str
    count: int
    syms: list[str]

    def __init__(self, name: str, desc: str, syms: list[str]) -> None:
        self.name = name
        self.desc = desc
        self.count = len(syms)
        self.syms = syms

    def __getitem__(self, name: str) -> Any:
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

        raise KeyError


class BaseGeneSetCollection(abc.ABC):
    """Base class for gene set collections."""

    @abc.abstractmethod
    def get_gene_set(self, gene_set_id: str) -> Optional[GeneSet]:
        """Return the gene set if found; returns None if not found."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_all_gene_sets(self) -> list[GeneSet]:
        """Return list of all gene sets in the collection."""
        raise NotImplementedError


class GeneSetCollection(
    GenomicResourceImplementation,
    ResourceConfigValidationMixin,
    InfoImplementationMixin,
    BaseGeneSetCollection,
):
    """Class representing a collection of gene sets in a resource."""

    def __init__(self, resource: GenomicResource) -> None:
        super().__init__(resource)

        self.config = self.validate_and_normalize_schema(
            self.config, resource,
        )
        config = resource.get_config()
        self.collection_id = self.config["id"]
        assert self.collection_id != "denovo"
        assert resource.get_type() == "gene_set", "Invalid resource type"
        self.web_label = config.get("web_label", None)
        self.web_format_str = config.get("web_format_str", None)
        logger.debug("loading %s: %s", self.collection_id, config)
        self.gene_sets: dict[str, GeneSet] = self.load_gene_sets()

        assert self.collection_id, self.gene_sets

    @property
    def files(self) -> set[str]:
        raise NotImplementedError

    def load_gene_sets(self) -> dict[str, GeneSet]:
        """Build a gene set collection from a given GenomicResource."""
        assert self.resource is not None
        gene_sets = {}
        config = self.resource.get_config()
        collection_format = config["format"]
        logger.debug("loading %s: %s", self.collection_id, config)

        if collection_format == "map":
            filename = self.config["filename"]
            names_filename = filename[:-4] + "names.txt"
            names_file = None
            if self.resource.file_exists(names_filename):
                names_file = self.resource.open_raw_file(names_filename)
            gene_terms = read_mapping_file(
                self.resource.open_raw_file(filename),
                names_file,
            )
        elif collection_format == "gmt":
            filename = config["filename"]
            gene_terms = read_gmt_file(self.resource.open_raw_file(filename))
        elif collection_format == "directory":
            directory = config["directory"]
            filepaths = []
            if directory == ".":
                directory = ""  # Easier check with startswith
            for filepath, _ in self.resource.get_manifest().get_files():
                if filepath.startswith(directory) and \
                        filepath.endswith(".txt"):
                    filepaths.append(filepath)

            files = [self.resource.open_raw_file(f) for f in filepaths]

            gene_terms = read_ewa_set_file(files)
        else:
            raise ValueError("Invalid collection format type")

        for key, value in gene_terms.tDesc.items():
            syms = list(gene_terms.t2G[key].keys())
            gene_set = GeneSet(key, value, syms)
            gene_sets[gene_set.name] = gene_set
        return gene_sets

    def get_gene_set(self, gene_set_id: str) -> Optional[GeneSet]:
        """Return the gene set if found; returns None if not found."""
        gene_set = self.gene_sets.get(gene_set_id)
        if gene_set is None:
            logger.warning(
                "%s not found in %s", gene_set_id, self.gene_sets.keys(),
            )
        return gene_set

    def get_all_gene_sets(self) -> list[GeneSet]:
        return list(self.gene_sets.values())

    def get_template(self) -> Template:
        return Template(textwrap.dedent("""
            {% extends base %}
            {% block content %}
            <hr>
            <h2>Gene set ID: {{ data["id"] }}</h2>
            {% if data["format"] == "directory" %}
            <h3>Gene sets directory:</h3>
            <a href="{{ data["directory"] }}">
            {{ data["directory"] }}
            </a>
            {% else %}
            <h3>Gene sets file:</h3>
            <a href="{{ data["filename"] }}">
            {{ data["filename"] }}
            </a>
            {% endif %}
            <p>Format: {{ data["format"] }}</p>
            {% if data["web_label"] %}
            <p>Web label: {{ data["web_label"] }}</p>
            {% endif %}
            {% if data["web_format_str"] %}
            <p>Web label: {{ data["web_format_str"] }}</p>
            {% endif %}
            {% endblock %}
        """))

    def _get_template_data(self) -> dict:
        info = copy.deepcopy(self.config)
        if "meta" in info:
            info["meta"] = markdown(str(info["meta"]))
        return info

    @staticmethod
    def get_schema() -> dict[str, Any]:
        return {
            **get_base_resource_schema(),
            "filename": {"type": "string"},
            "id": {"type": "string"},
            "directory": {"type": "string"},
            "format": {"type": "string"},
            "web_label": {"type": "string"},
            "web_format_str": {"type": "string"},

        }

    def get_info(self, **kwargs: Any) -> str:  # noqa: ARG002
        return InfoImplementationMixin.get_info(self)

    def calc_info_hash(self) -> bytes:
        return b"placeholder"

    def calc_statistics_hash(self) -> bytes:
        return b"placeholder"

    def add_statistics_build_tasks(
        self, task_graph: TaskGraph, **kwargs: Any,
    ) -> list[Task]:
        return []


# class SqliteGeneSetCollectionDB(
#     GenomicResourceImplementation,
#     ResourceConfigValidationMixin,
#     InfoImplementationMixin
# ):
#     """Collection of gene sets stored in a SQLite database."""

#     def __init__(self, resource):
#         super().__init__(resource)
#         self.config = self.validate_and_normalize_schema(
#             self.config, resource
#         )
#         self.collection_id = self.config["id"]
#         assert self.collection_id != "denovo"
#         assert resource.get_type() == "gene_set", "Invalid resource type"
#         self.web_label = self.config.get("web_label", None)
#         self.web_format_str = self.config.get("web_format_str", None)
#         self.dbfile = self._get_dbfile_path()
#         self.engine = create_engine(f"sqlite:///{self.dbfile}")
#         self.metadata = MetaData(self.engine)
#         self._create_gene_sets_table()

#     def _get_dbfile_path(self) -> str:
#         dbfile = self.config["dbfile"]
#         proto: FsspecReadOnlyProtocol = \
#             cast(FsspecReadOnlyProtocol, self.resource.proto)
#         if not isinstance(proto, FsspecReadOnlyProtocol) \
#                 and proto.scheme != "file":
#             raise ValueError(
#                 "sqlite gene sets are supported only on local filesystem")
#         dbfile_url = proto.get_resource_file_url(self.resource, dbfile)
#         dbfile_path = urlparse(dbfile_url).path
#         return dbfile_path

#     def _create_gene_sets_table(self):
#         self.gene_sets_table = Table(
#             "gene_sets",
#             self.metadata,
#             Column("name", String(), primary_key=True),
#             Column("desc", String()),
#             Column("syms", String()),
#         )

#         self.metadata.create_all(self.engine)

#     def add_gene_set(self, gene_set: GeneSet):
#         """Add a gene set to the database."""
#         with self.engine.begin() as connection:
#             insert_values = {
#                 "name": gene_set.name,
#                 "desc": gene_set.desc,
#                 "syms": ",".join(gene_set.syms)
#             }
#             connection.execute(
#                 insert(self.gene_sets_table).values(insert_values)
#             )
#             connection.commit()

#     def get_gene_set(self, gene_set_id):
#         """Fetch and construct a GeneSet from the database."""
#         table = self.gene_sets_table
#         select = table.select().where(table.c.name == gene_set_id)
#         with self.engine.connect() as connection:
#             row = connection.execute(select).fetchone()
#             gene_set = GeneSet(
#                 row["name"],
#                 row["desc"],
#                 row["syms"].split(",")
#             )
#             return gene_set

#     def get_template(self):
#         return Template(textwrap.dedent("""
#             {% extends base %}
#             {% block content %}
#             <hr>
#             <h3>Gene sets dbfile:</h3>
#             <a href="{{ data["dbfile"] }}">
#             {{ data["dbfile"] }}
#             </a>
#             <p>Format: {{ data["format"] }}</p>
#             {% if data["web_label"] %}
#             <p>Web label: {{ data["web_label"] }}</p>
#             {% endif %}
#             {% if data["web_format_str"] %}
#             <p>Web label: {{ data["web_format_str"] }}</p>
#             {% endif %}
#             {% endblock %}
#         """))

#     def _get_template_data(self):
#         info = copy.deepcopy(self.config)
#         if "meta" in info:
#             info["meta"] = markdown(str(info["meta"]))
#         return info

#     @property
#     def files(self):
#         raise NotImplementedError

#     @staticmethod
#     def get_schema():
#         return {
#             **get_base_resource_schema(),
#             "dbfile": {"type": "string"},
#             "id": {"type": "string"},
#             "format": {"type": "string"},
#             "web_label": {"type": "string"},
#             "web_format_str": {"type": "string"}

#         }

#     def get_info(self):
#         return InfoImplementationMixin.get_info(self)

#     def calc_info_hash(self):
#         return "placeholder"

#     def calc_statistics_hash(self) -> bytes:
#         return b"placeholder"

#     def add_statistics_build_tasks(self, task_graph, **kwargs) -> list[Task]:
#         return []


class GeneSetsDb:
    """Class that represents a dictionary of gene set collections."""

    def __init__(self, gene_set_collections: list[GeneSetCollection]) -> None:
        self.gene_set_collections: dict[str, GeneSetCollection] = {
            gsc.collection_id: gsc
            for gsc in gene_set_collections
        }

    @cached_property
    def collections_descriptions(self) -> list[dict[str, Any]]:
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
                },
            )
        return gene_sets_collections_desc

    def has_gene_set_collection(self, gsc_id: str) -> bool:
        """Check the database if contains the specified gene set collection."""
        return gsc_id in self.gene_set_collections

    def get_gene_set_collection_ids(self) -> set[str]:
        """Return all gene set collection ids.

        Including the ids of collections which have not been loaded.
        """
        return set(self.gene_set_collections.keys())

    def get_gene_set_ids(self, collection_id: str) -> set[str]:
        """Return the IDs of all the gene sets in specified collection."""
        gsc = self.gene_set_collections[collection_id]
        return set(gsc.gene_sets.keys())

    def get_all_gene_sets(self, collection_id: str) -> list[GeneSet]:
        """Return all the gene sets in the specified collection."""
        gsc = self.gene_set_collections[collection_id]
        logger.debug(
            "gene sets from %s: %s", collection_id, len(gsc.gene_sets.keys()))
        return list(gsc.gene_sets.values())

    def get_gene_set(
        self, collection_id: str,
        gene_set_id: str,
    ) -> Optional[GeneSet]:
        """Find and return a gene set in a gene set collection."""
        gsc = self.gene_set_collections[collection_id]
        return gsc.get_gene_set(gene_set_id)

    def __len__(self) -> int:
        return len(self.gene_set_collections)


def build_gene_set_collection_from_file(
        filename: str,
        collection_id: Optional[str] = None,
        collection_format: Optional[str] = None,
        web_label: Optional[str] = None,
        web_format_str: Optional[str] = None,
) -> GeneSetCollection:
    """Return a Gene Set Collection by adapting a file to a local resource."""
    dirname = os.path.dirname(filename)
    basename = os.path.basename(filename)
    if collection_format is None:
        is_dir = os.path.isdir(filename)
        if is_dir:
            collection_format = "directory"
        else:
            extension = os.path.splitext(filename)[1]
            if extension == ".txt":
                collection_format = "map"
            elif extension == ".gmt":
                collection_format = "gmt"
            elif extension == ".sql":
                collection_format = "sqlite"
            else:
                raise ValueError("Cannot find collection format automatically")

    if collection_id is None:
        collection_id = basename

    config = {
        "type": "gene_set",
        "id": collection_id,
        "format": collection_format,
        "web_label": web_label,
        "web_format_str": web_format_str,
    }
    if collection_format == "directory":
        config["directory"] = basename
    elif collection_format == "sqlite":
        config["dbfile"] = basename
    else:
        config["filename"] = basename
    resource = build_local_resource(dirname, config)
    return build_gene_set_collection_from_resource(resource)


def build_gene_set_collection_from_resource(
    resource: GenomicResource,
) -> GeneSetCollection:
    """Return a Gene Set Collection built from a resource."""
    if resource is None:
        raise ValueError(f"missing resource {resource}")

    return GeneSetCollection(resource)
