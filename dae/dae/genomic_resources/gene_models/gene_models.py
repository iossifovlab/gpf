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
from dae.genomic_resources.utils import build_chrom_mapping
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
    """Manage and query gene model data from genomic resources.

    This class provides access to gene models loaded from various file formats
    (GTF, refFlat, refSeq, CCDS, etc.) and offers efficient querying by gene
    name or genomic location.

    The class maintains three internal data structures:
    - transcript_models: Dict mapping transcript IDs to TranscriptModel objects
    - gene_models: Dict mapping gene names to lists of TranscriptModel objects
    - _tx_index: IntervalTree index for fast location-based queries

    Attributes:
        resource (GenomicResource): The genomic resource containing gene models.
        config (dict): Validated configuration from the resource.
        reference_genome_id (str | None): ID of the reference genome.
        gene_models (dict[str, list[TranscriptModel]]): Gene name to
            transcript models mapping.
        transcript_models (dict[str, TranscriptModel]): Transcript ID to
            transcript model mapping.

    Example:
        >>> from dae.genomic_resources.gene_models.gene_models_factory import \\
        ...     build_gene_models_from_file
        >>> gene_models = build_gene_models_from_file("genes.gtf")
        >>> gene_models.load()
        >>> # Query by gene name
        >>> tp53_transcripts = gene_models.gene_models_by_gene_name("TP53")
        >>> # Query by location
        >>> transcripts = gene_models.gene_models_by_location("chr17", 7676592)

    Note:
        The gene models must be loaded using the load() method before queries
        can be performed. The class is thread-safe for concurrent access.
    """

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

        self._reset()
        self.__lock = Lock()

    @property
    def resource_id(self) -> str:
        return self.resource.resource_id

    def close(self) -> None:
        pass

    def _reset(self) -> None:
        """Reset gene models."""
        self._is_loaded = False

        self.transcript_models = {}
        self.gene_models = defaultdict(list)
        self._tx_index = defaultdict(IntervalTree)

    def _add_to_utr_index(self, tm: TranscriptModel) -> None:
        self._tx_index[tm.chrom].add(Interval(tm.tx[0], tm.tx[1] + 1, tm))

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

    def _update_indexes(self) -> None:
        """Update internal indexes."""
        self.gene_models = defaultdict(list)
        self._tx_index = defaultdict(IntervalTree)
        for transcript in self.transcript_models.values():
            self.gene_models[transcript.gene].append(transcript)
            self._add_to_utr_index(transcript)

    def gene_names(self) -> list[str]:
        """Get list of all gene names in the loaded gene models.

        Returns:
            list[str]: List of gene names (symbols).

        Example:
            >>> gene_models.load()
            >>> genes = gene_models.gene_names()
            >>> print(f"Loaded {len(genes)} genes")
        """
        if self.gene_models is None:
            logger.warning(
                "gene models %s are empty", self.resource.resource_id)
            return []

        return list(self.gene_models.keys())

    def gene_models_by_gene_name(
        self, name: str,
    ) -> list[TranscriptModel] | None:
        """Retrieve all transcript models for a specific gene.

        Args:
            name (str): The gene name/symbol to search for.

        Returns:
            list[TranscriptModel] | None: List of transcript models for the
                gene, or None if the gene is not found.

        Example:
            >>> transcripts = gene_models.gene_models_by_gene_name("BRCA1")
            >>> if transcripts:
            ...     print(f"BRCA1 has {len(transcripts)} transcript variants")
        """
        return self.gene_models.get(name, None)

    def has_chromosome(self, chrom: str) -> bool:
        """Check if a chromosome has any gene models.

        Args:
            chrom (str): The chromosome name to check.

        Returns:
            bool: True if the chromosome has gene models, False otherwise.

        Example:
            >>> if gene_models.has_chromosome("chr1"):
            ...     print("Chromosome 1 has gene annotations")
        """
        return chrom in self._tx_index

    def gene_models_by_location(
        self, chrom: str, pos_begin: int, pos_end: int | None = None,
    ) -> list[TranscriptModel]:
        """Retrieve transcripts overlapping a genomic position or region.

        This method uses an interval tree index for efficient querying of
        transcripts by genomic coordinates.

        Args:
            chrom (str): The chromosome name (e.g., "chr1", "17").
            pos_begin (int): The start position (1-based, inclusive).
            pos_end (int | None): The end position (1-based, inclusive).
                If None, queries a single position.

        Returns:
            list[TranscriptModel]: List of TranscriptModel objects whose
                transcript regions overlap the query position/region.
                Returns empty list if no overlaps found.

        Example:
            >>> # Query single position
            >>> models = gene_models.gene_models_by_location("chr17", 7676592)
            >>> # Query region
            >>> models = gene_models.gene_models_by_location(
            ...     "chr17", 7661779, 7687550
            ... )
            >>> for tm in models:
            ...     print(f"{tm.gene}: {tm.tr_id}")

        Note:
            Positions are swapped automatically if pos_end < pos_begin.
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

    @staticmethod
    def get_schema() -> dict[str, Any]:
        return {
            **get_base_resource_schema(),
            "filename": {"type": "string"},
            "format": {"type": "string"},
            "gene_mapping": {"type": "string"},
            "chrom_mapping": {"type": "dict", "schema": {
                "filename": {
                    "type": "string",
                    "excludes": ["add_prefix", "del_prefix"],
                },
                "add_prefix": {"type": "string"},
                "del_prefix": {"type": "string", "excludes": "add_prefix"},
            }},
        }

    def load(self) -> GeneModels:
        """Load gene models from the genomic resource.

        This method parses the gene model file and builds internal indexes
        for efficient querying. It is thread-safe and will only load once.

        Returns:
            GeneModels: Self, for method chaining.

        Example:
            >>> gene_models = build_gene_models_from_file("genes.gtf")
            >>> gene_models.load()
            >>> num_transcripts = len(gene_models.transcript_models)
            >>> print(f"Loaded {num_transcripts} transcripts")

        Note:
            Calling load() multiple times is safe - subsequent calls return
            immediately if already loaded.
        """
        with self.__lock:
            if self._is_loaded:
                return self
            self._reset()
            transcript_models = load_transcript_models(self.resource)
            self.transcript_models = self._chrom_mapping(transcript_models)
            self._update_indexes()
            self._is_loaded = True
            return self

    def _chrom_mapping(
        self, transcript_models: dict[str, TranscriptModel],
    ) -> dict[str, TranscriptModel]:
        chrom_mapping = build_chrom_mapping(self.resource)
        if chrom_mapping is None:
            return transcript_models

        result = {}
        for tm in transcript_models.values():
            chrom = chrom_mapping(tm.chrom)
            if chrom is None:
                logger.warning(
                        "transcript %s on chrom %s is removed by "
                        "chrom_mapping",
                        tm.tr_id, tm.chrom,
                    )
                continue
            tm.chrom = chrom
            result[tm.tr_id] = tm
        return result

    def is_loaded(self) -> bool:
        """Check if gene models have been loaded.

        Returns:
            bool: True if load() has been called and completed, False otherwise.

        Example:
            >>> if not gene_models.is_loaded():
            ...     gene_models.load()
        """
        with self.__lock:
            return self._is_loaded

    @staticmethod
    def join_gene_models(*gene_models: GeneModels) -> GeneModels:
        """Merge multiple gene models into a single GeneModels object.

        This combines transcript models from multiple sources into one
        unified gene models object.

        Args:
            *gene_models (GeneModels): Two or more GeneModels objects to merge.

        Returns:
            GeneModels: New GeneModels object containing all transcripts.

        Raises:
            ValueError: If fewer than 2 gene models provided.

        Example:
            >>> gm1 = build_gene_models_from_file("genes1.gtf")
            >>> gm2 = build_gene_models_from_file("genes2.gtf")
            >>> merged = GeneModels.join_gene_models(gm1, gm2)

        Note:
            Transcript IDs should be unique across all input gene models.
        """
        if len(gene_models) < 2:
            raise ValueError("The function needs at least 2 arguments!")

        gm = GeneModels(gene_models[0].resource)
        gm._reset()

        gm.transcript_models = gene_models[0].transcript_models.copy()

        for i in gene_models[1:]:
            gm.transcript_models.update(i.transcript_models)

        gm._update_indexes()

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
