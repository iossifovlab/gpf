from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Generator
from threading import Lock
from typing import Any, cast

from intervaltree import (  # type: ignore
    Interval,
    IntervalTree,
)

from dae.genomic_resources.repository import (
    GenomicResource,
)
from dae.genomic_resources.resource_implementation import (
    ResourceConfigValidationMixin,
    get_base_resource_schema,
)
from dae.utils.regions import (
    Region,
    collapse,
)

from .parsers import load_transcript_models
from .transcript_models import TranscriptModel

logger = logging.getLogger(__name__)


class GeneModels(
    ResourceConfigValidationMixin,
):
    """Provides class for gene models."""

    def __init__(self, resource: GenomicResource):
        self._is_loaded = False
        if resource.get_type() != "gene_models":
            raise ValueError(
                f"wrong type of resource passed: {resource.get_type()}")
        self.resource = resource
        self.config = self.validate_and_normalize_schema(
            resource.get_config(), resource,
        )

        self.reference_genome_id: str | None = \
            self.config["meta"]["labels"].get("reference_genome") \
            if (self.config.get("meta") is not None
                and self.config["meta"].get("labels") is not None) \
            else None

        self.gene_models: dict[str, list[TranscriptModel]] = defaultdict(list)
        self._tx_index: dict[str, IntervalTree] = defaultdict(IntervalTree)
        self.transcript_models: dict[str, Any] = {}

        self.reset()
        self.__lock = Lock()

    @property
    def resource_id(self) -> str:
        return self.resource.resource_id

    def close(self) -> None:
        pass

    def reset(self) -> None:
        """Reset gene models."""
        self._is_loaded = False

        self.transcript_models = {}
        self.gene_models = defaultdict(list)
        self._tx_index = defaultdict(IntervalTree)

    def _add_to_utr_index(self, tm: TranscriptModel) -> None:
        self._tx_index[tm.chrom].add(Interval(tm.tx[0], tm.tx[1] + 1, tm))

    def _add_transcript_model(self, transcript_model: TranscriptModel) -> None:
        """Add a transcript model to the gene models."""
        assert transcript_model.tr_id not in self.transcript_models
        self.transcript_models[transcript_model.tr_id] = transcript_model

    def chrom_gene_models(self) -> Generator[
            tuple[tuple[str, str], list[TranscriptModel]], None, None]:
        """Generate chromosome and gene name keys with transcript models."""
        for chrom, interval_tree in self._tx_index.items():
            gene_models: dict[
                tuple[str, str], list[TranscriptModel]] = defaultdict(list)
            for interval in interval_tree:
                tm = cast(TranscriptModel, interval.data)
                assert chrom == tm.chrom
                gene_models[tm.chrom, tm.gene].append(tm)
            yield from gene_models.items()

    def update_indexes(self) -> None:
        """Update internal indexes."""
        self.gene_models = defaultdict(list)
        self._tx_index = defaultdict(IntervalTree)
        for transcript in self.transcript_models.values():
            self.gene_models[transcript.gene].append(transcript)
            self._add_to_utr_index(transcript)

    def gene_names(self) -> list[str]:
        if self.gene_models is None:
            logger.warning(
                "gene models %s are empty", self.resource.resource_id)
            return []

        return list(self.gene_models.keys())

    def gene_models_by_gene_name(
        self, name: str,
    ) -> list[TranscriptModel] | None:
        return self.gene_models.get(name, None)

    def has_chromosome(self, chrom: str) -> bool:
        return chrom in self._tx_index

    def gene_models_by_location(
        self, chrom: str, pos_begin: int, pos_end: int | None = None,
    ) -> list[TranscriptModel]:
        """Retrieve TranscriptModel objects based on a single genomic position.

        Args:
            chrom (str): The chromosome name.
            pos (int): The genomic position.

        Returns:
            list[TranscriptModel]: A list of TranscriptModel objects that
                contain the given position.
        """
        if chrom not in self._tx_index:
            return []

        if pos_end is None:
            pos_end = pos_begin
        if pos_end < pos_begin:
            pos_begin, pos_end = pos_end, pos_begin
        tms_interval = self._tx_index[chrom]
        result = tms_interval.overlap(pos_begin, pos_end + 1)

        return [r.data for r in result]

    def relabel_chromosomes(
        self, relabel: dict[str, str] | None = None,
        map_file: str | None = None,
    ) -> None:
        """Relabel chromosomes in gene model."""
        assert relabel or map_file
        if not relabel:
            assert map_file is not None
            with open(map_file) as infile:
                relabel = dict(
                    line.strip("\n\r").split()[:2]for line in infile
                )

        self.transcript_models = {
            tid: tm
            for tid, tm in self.transcript_models.items()
            if tm.chrom in relabel
        }

        for transcript_model in self.transcript_models.values():
            transcript_model.chrom = relabel[transcript_model.chrom]

        self.update_indexes()

    @staticmethod
    def get_schema() -> dict[str, Any]:
        return {
            **get_base_resource_schema(),
            "filename": {"type": "string"},
            "format": {"type": "string"},
            "gene_mapping": {"type": "string"},
        }

    def load(self) -> GeneModels:
        """Load gene models."""
        with self.__lock:
            if self._is_loaded:
                return self
            self.reset()
            self.transcript_models = load_transcript_models(self.resource)
            self.update_indexes()
            self._is_loaded = True
            return self

    def is_loaded(self) -> bool:
        """Check if gene models are loaded."""
        with self.__lock:
            return self._is_loaded


def join_gene_models(*gene_models: GeneModels) -> GeneModels:
    """Join muliple gene models into a single gene models object."""
    if len(gene_models) < 2:
        raise ValueError("The function needs at least 2 arguments!")

    gm = GeneModels(gene_models[0].resource)
    gm.reset()

    gm.transcript_models = gene_models[0].transcript_models.copy()

    for i in gene_models[1:]:
        gm.transcript_models.update(i.transcript_models)

    gm.update_indexes()

    return gm


def create_regions_from_genes(
    gene_models: GeneModels,
    genes: list[str],
    regions: list[Region] | None,
    gene_regions_heuristic_cutoff: int = 20,
    gene_regions_heuristic_extend: int = 20000,
) -> list[Region] | None:
    """Produce a list of regions from given gene symbols.

    If given a list of regions, will merge the newly-created regions
    from the genes with the provided ones.
    """
    assert genes is not None
    assert gene_models is not None

    if len(genes) == 0 or len(genes) > gene_regions_heuristic_cutoff:
        return regions

    gene_regions = []
    for gene_name in genes:
        gene_model = gene_models.gene_models_by_gene_name(gene_name)
        if gene_model is None:
            logger.warning("gene model for %s not found", gene_name)
            continue
        for gm in gene_model:
            gene_regions.append(  # noqa: PERF401
                Region(
                    gm.chrom,
                    max(1, gm.tx[0] - 1 - gene_regions_heuristic_extend),
                    gm.tx[1] + 1 + gene_regions_heuristic_extend,
                ),
            )

    gene_regions = collapse(gene_regions)
    if not regions:
        regions = gene_regions or None
    else:
        result = []
        for gene_region in gene_regions:
            for region in regions:
                intersection = gene_region.intersection(region)
                if intersection:
                    result.append(intersection)
        result = collapse(result)
        logger.info("original regions: %s; result: %s", regions, result)
        regions = result

    return regions
