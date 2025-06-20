"""Classes for handling of gene sets."""

import abc
import logging
import os
from collections.abc import Sequence
from functools import cached_property
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

from dae.gene_sets.gene_term import (
    read_ewa_set_file,
    read_gmt_file,
    read_mapping_file,
)
from dae.genomic_resources.fsspec_protocol import build_local_resource
from dae.genomic_resources.repository import (
    GenomicResource,
    GenomicResourceRepo,
)
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.task_graph.graph import Task, TaskGraph

logger = logging.getLogger(__name__)


class MetaSchema(BaseModel):
    description: str | None = None
    labels: dict[str, Any] | None = None


class BaseResourceSchema(BaseModel):
    type: str | None = None
    meta: MetaSchema | None = None


class ViewRangeSchema(BaseModel):
    min: float | None = None
    max: float | None = None


# pylint: disable=missing-class-docstring
class NumericHistogramSchema(BaseModel):
    type: Literal["number"]
    plot_function: str | None = None
    number_of_bins: int | None = None
    view_range: ViewRangeSchema | None = None
    x_log_scale: bool | None = None
    y_log_scale: bool | None = None
    x_min_log: float | None = None
    value_order: list[str | int] | None = None
    displayed_values_count: int | None = None


# pylint: disable=missing-class-docstring
class CategoricalHistogramSchema(BaseModel):
    type: Literal["categorical"]
    displayed_values_count: int | None = None
    displayed_values_percent: float | None = None
    value_order: list[str | int] | None = None
    y_log_scale: bool | None = None
    label_rotation: int | None = None
    plot_function: str | None = None
    enforce_type: bool | None = None
    natural_order: bool | None = None


HistogramConfig = Annotated[
    NumericHistogramSchema | CategoricalHistogramSchema,
    Field(discriminator="type"),
]


# pylint: disable=missing-class-docstring
class GeneSetResourceSchema(BaseModel):
    resource_id: str = Field(alias="id")
    filename: str | None = None
    directory: str | None = None
    resource_format: str | None = Field(alias="format")
    web_label: str | None = None
    web_format_str: str | None = None
    histograms: dict[
        Literal["genes_per_gene_set", "gene_sets_per_gene"],
        HistogramConfig,
    ] | None = None


class GeneSet:
    """Class representing a set of genes."""

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
    def __init__(self, collection_id: str) -> None:
        self.collection_id = collection_id
        self.web_label: str = ""
        self.web_format_str: str = ""
        self.gene_sets: dict[str, GeneSet] = {}

    @abc.abstractmethod
    def get_gene_set(self, gene_set_id: str) -> GeneSet | None:
        """Return the gene set if found; returns None if not found."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_all_gene_sets(self) -> list[GeneSet]:
        """Return list of all gene sets in the collection."""
        raise NotImplementedError


class GeneSetCollection(
    BaseGeneSetCollection,
):
    """Class representing a collection of gene sets in a resource."""

    def __init__(self, resource: GenomicResource) -> None:
        config = resource.get_config()
        if config is None:
            raise ValueError(
                f"genomic resource {resource.resource_id} not configured")
        self.resource = resource

        self.config = GeneSetResourceSchema.model_validate(config)
        super().__init__(self.config.resource_id)

        assert self.collection_id != "denovo"
        if resource.get_type() not in {"gene_set_collection", "gene_set"}:
            raise ValueError("Invalid resource type for gene set collection")
        if resource.get_type() == "gene_set":
            logger.warning(
                "'gene_set' resource type is deprecated; "
                "use 'gene_set_collection' instead")

        self.web_label = self.config.web_label or ""
        self.web_format_str = self.config.web_format_str or ""
        logger.debug("loading %s: %s", self.collection_id, config)
        self.gene_sets: dict[str, GeneSet] = self.load_gene_sets()

        assert self.collection_id, self.gene_sets

    @property
    def files(self) -> set[str]:
        """Return a list of resource files the implementation utilises."""
        res = set()
        collection_format = self.config.resource_format

        if collection_format == "map":
            filename = self.config.filename
            assert filename is not None
            res.add(filename)
            names_filename = filename[:-4] + "names.txt"
            if self.resource.file_exists(names_filename):
                res.add(names_filename)
        elif collection_format == "gmt":
            filename = self.config.filename
            assert filename is not None
            res.add(filename)
        elif collection_format == "directory":
            directory = self.config.directory
            assert directory is not None
            if directory == ".":
                directory = ""
            for filepath, _ in self.resource.get_manifest().get_files():
                if filepath.startswith(directory) and \
                        filepath.endswith(".txt"):
                    res.add(filepath)
        else:
            raise ValueError("Invalid collection format type")

        return res

    def load_gene_sets(self) -> dict[str, GeneSet]:
        """Build a gene set collection from a given GenomicResource."""
        assert self.resource is not None
        gene_sets = {}
        collection_format = self.config.resource_format
        logger.debug("loading %s", self.collection_id)

        if collection_format == "map":
            filename = self.config.filename
            assert filename is not None
            names_filename = filename[:-4] + "names.txt"
            names_file = None
            if self.resource.file_exists(names_filename):
                names_file = self.resource.open_raw_file(names_filename)
            gene_terms = read_mapping_file(
                self.resource.open_raw_file(filename),
                names_file,
            )
        elif collection_format == "gmt":
            filename = self.config.filename
            assert filename is not None
            gene_terms = read_gmt_file(self.resource.open_raw_file(filename))
        elif collection_format == "directory":
            directory = self.config.directory
            assert directory is not None
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

        for key, value in gene_terms.t_desc.items():
            syms = list(gene_terms.t2g[key].keys())
            gene_set = GeneSet(key, value, syms)
            gene_sets[gene_set.name] = gene_set
        return gene_sets

    def get_gene_set(self, gene_set_id: str) -> GeneSet | None:
        """Return the gene set if found; returns None if not found."""
        gene_set = self.gene_sets.get(gene_set_id)
        if gene_set is None:
            logger.warning(
                "%s not found in %s", gene_set_id, self.gene_sets.keys(),
            )
        return gene_set

    def get_all_gene_sets(self) -> list[GeneSet]:
        return list(self.gene_sets.values())

    def calc_info_hash(self) -> bytes:
        return b"placeholder"

    def calc_statistics_hash(self) -> bytes:
        return b"placeholder"

    def add_statistics_build_tasks(
        self, task_graph: TaskGraph, **kwargs: Any,  # noqa: ARG002
    ) -> list[Task]:
        return []

    def get_genes_per_gene_set_hist_filename(self) -> str:
        return "statistics/genes_per_gene_set_histogram.png"

    def get_gene_sets_per_gene_hist_filename(self) -> str:
        return "statistics/gene_sets_per_gene_histogram.png"


class GeneSetsDb:
    """Class that represents a dictionary of gene set collections."""

    def __init__(
        self,
        gene_set_collections: Sequence[BaseGeneSetCollection],
    ) -> None:
        self.gene_set_collections: dict[str, BaseGeneSetCollection] = {
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
        return gsc.get_all_gene_sets()

    def get_gene_set(
        self, collection_id: str,
        gene_set_id: str,
    ) -> GeneSet | None:
        """Find and return a gene set in a gene set collection."""
        gsc = self.gene_set_collections[collection_id]
        return gsc.get_gene_set(gene_set_id)

    def __len__(self) -> int:
        return len(self.gene_set_collections)


def build_gene_set_collection_from_file(
        filename: str,
        collection_id: str | None = None,
        collection_format: str | None = None,
        web_label: str | None = None,
        web_format_str: str | None = None,
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


def build_gene_set_collection_from_resource_id(
    resource_id: str, grr: GenomicResourceRepo | None = None,
) -> GeneSetCollection:
    if grr is None:
        grr = build_genomic_resource_repository()
    return build_gene_set_collection_from_resource(
        grr.get_resource(resource_id))
