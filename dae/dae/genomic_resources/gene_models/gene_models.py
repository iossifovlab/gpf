from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, cast

from dae.genomic_resources import GenomicResource
from dae.genomic_resources.fsspec_protocol import build_local_resource
from dae.genomic_resources.resource_implementation import (
    ResourceConfigValidationMixin,
    get_base_resource_schema,
)
from dae.utils.regions import (
    BedRegion,
    Region,
    collapse,
)

logger = logging.getLogger(__name__)


class Exon:
    """Provides exon model."""

    def __init__(
        self,
        start: int,
        stop: int,
        frame: int | None = None,
    ):
        """Initialize exon model.

        Args:
            start: The genomic start position of the exon (1-based).
            stop (int): The genomic stop position of the exon (1-based, closed).
            frame (Optional[int]): The frame of the exon.
        """

        self.start = start
        self.stop = stop
        self.frame = frame  # related to cds

    def __repr__(self) -> str:
        return f"Exon(start={self.start}; stop={self.stop})"

    def contains(self, region: tuple[int, int]) -> bool:
        start, stop = region
        return self.start <= start and self.stop >= stop


class TranscriptModel:
    """Provides transcript model."""

    def __init__(
        self,
        gene: str,
        tr_id: str,
        tr_name: str,
        chrom: str,
        strand: str,
        tx: tuple[int, int],  # pylint: disable=invalid-name
        cds: tuple[int, int],
        exons: list[Exon] | None = None,
        attributes: dict[str, Any] | None = None,
    ):
        """Initialize transcript model.

        Args:
            gene (str): The gene name.
            tr_id (str): The transcript ID.
            tr_name (str): The transcript name.
            chrom (str): The chromosome name.
            strand (str): The strand of the transcript.
            tx (tuple[int, int]): The transcript start and end positions.
                (1-based, closed interval)
            cds (tuple[int, int]): The coding region start and end positions.
                The CDS region includes the start and stop codons.
                (1-based, closed interval)
            exons (Optional[list[Exon]]): The list of exons. Defaults to
                empty list.
            attributes (Optional[dict[str, Any]]): The additional attributes.
                Defaults to empty dictionary.
        """
        self.gene = gene
        self.tr_id = tr_id
        self.tr_name = tr_name
        self.chrom = chrom
        self.strand = strand
        self.tx = tx  # pylint: disable=invalid-name
        self.cds = cds
        self.exons: list[Exon] = exons if exons is not None else []
        self.attributes = attributes if attributes is not None else {}

    def is_coding(self) -> bool:
        return self.cds[0] < self.cds[1]

    def cds_regions(self, ss_extend: int = 0) -> list[BedRegion]:
        """Compute CDS regions."""
        if self.cds[0] >= self.cds[1]:
            return []

        regions = []
        k = 0
        while self.exons[k].stop < self.cds[0]:
            k += 1

        if self.cds[1] <= self.exons[k].stop:
            regions.append(
                BedRegion(
                    chrom=self.chrom, start=self.cds[0], stop=self.cds[1]),
            )
            return regions

        regions.append(
            BedRegion(
                chrom=self.chrom,
                start=self.cds[0],
                stop=self.exons[k].stop + ss_extend,
            ),
        )
        k += 1
        while k < len(self.exons) and self.exons[k].stop <= self.cds[1]:
            if self.exons[k].stop < self.cds[1]:
                regions.append(
                    BedRegion(
                        chrom=self.chrom,
                        start=self.exons[k].start - ss_extend,
                        stop=self.exons[k].stop + ss_extend,
                    ),
                )
                k += 1
            else:
                regions.append(
                    BedRegion(
                        chrom=self.chrom,
                        start=self.exons[k].start - ss_extend,
                        stop=self.exons[k].stop,
                    ),
                )
                return regions

        if k < len(self.exons) and self.exons[k].start <= self.cds[1]:
            regions.append(
                BedRegion(
                    chrom=self.chrom,
                    start=self.exons[k].start - ss_extend,
                    stop=self.cds[1],
                ),
            )

        return regions

    def utr5_regions(self) -> list[BedRegion]:
        """Build list of UTR5 regions."""
        if self.cds[0] >= self.cds[1]:
            return []

        regions = []
        k = 0
        if self.strand == "+":
            while self.exons[k].stop < self.cds[0]:
                regions.append(
                    BedRegion(
                        chrom=self.chrom,
                        start=self.exons[k].start,
                        stop=self.exons[k].stop,
                    ),
                )
                k += 1
            if self.exons[k].start < self.cds[0]:
                regions.append(
                    BedRegion(
                        chrom=self.chrom,
                        start=self.exons[k].start,
                        stop=self.cds[0] - 1,
                    ),
                )

        else:
            while self.exons[k].stop < self.cds[1]:
                k += 1
            if self.exons[k].stop == self.cds[1]:
                k += 1
            else:
                regions.append(
                    BedRegion(
                        chrom=self.chrom,
                        start=self.cds[1] + 1,
                        stop=self.exons[k].stop,
                    ),
                )
                k += 1

            regions.extend([
                BedRegion(chrom=self.chrom, start=exon.start, stop=exon.stop)
                for exon in self.exons[k:]
            ])

        return regions

    def utr3_regions(self) -> list[BedRegion]:
        """Build and return list of UTR3 regions."""
        if self.cds[0] >= self.cds[1]:
            return []

        regions = []
        k = 0
        if self.strand == "-":
            while self.exons[k].stop < self.cds[0]:
                regions.append(
                    BedRegion(
                        chrom=self.chrom,
                        start=self.exons[k].start,
                        stop=self.exons[k].stop,
                    ),
                )
                k += 1
            if self.exons[k].start < self.cds[0]:
                regions.append(
                    BedRegion(
                        chrom=self.chrom,
                        start=self.exons[k].start,
                        stop=self.cds[0] - 1,
                    ),
                )

        else:
            while self.exons[k].stop < self.cds[1]:
                k += 1
            if self.exons[k].stop == self.cds[1]:
                k += 1
            else:
                regions.append(
                    BedRegion(
                        chrom=self.chrom,
                        start=self.cds[1] + 1,
                        stop=self.exons[k].stop,
                    ),
                )
                k += 1

            regions.extend([
                BedRegion(chrom=self.chrom, start=exon.start, stop=exon.stop)
                for exon in self.exons[k:]
            ])

        return regions

    def all_regions(
        self, ss_extend: int = 0, prom: int = 0,
    ) -> list[BedRegion]:
        """Build and return list of regions."""
        # pylint:disable=too-many-branches
        regions = []

        if ss_extend == 0:
            regions.extend([
                BedRegion(chrom=self.chrom, start=exon.start, stop=exon.stop)
                for exon in self.exons
            ])

        else:
            for exon in self.exons:
                if exon.stop <= self.cds[0]:
                    regions.append(
                        BedRegion(
                            chrom=self.chrom,
                            start=exon.start, stop=exon.stop),
                    )
                elif exon.start <= self.cds[0]:
                    if exon.stop >= self.cds[1]:
                        regions.append(
                            BedRegion(
                                chrom=self.chrom,
                                start=exon.start, stop=exon.stop),
                        )
                    else:
                        regions.append(
                            BedRegion(
                                chrom=self.chrom,
                                start=exon.start,
                                stop=exon.stop + ss_extend,
                            ),
                        )
                elif exon.start > self.cds[1]:
                    regions.append(
                        BedRegion(
                            chrom=self.chrom, start=exon.start, stop=exon.stop),
                    )
                else:
                    if exon.stop >= self.cds[1]:
                        regions.append(
                            BedRegion(
                                chrom=self.chrom,
                                start=exon.start - ss_extend,
                                stop=exon.stop,
                            ),
                        )
                    else:
                        regions.append(
                            BedRegion(
                                chrom=self.chrom,
                                start=exon.start - ss_extend,
                                stop=exon.stop + ss_extend,
                            ),
                        )

        if prom != 0:
            if self.strand == "+":
                regions[0] = BedRegion(
                    chrom=regions[0].chrom,
                    start=regions[0].start - prom,
                    stop=regions[0].stop,
                )
            else:
                regions[-1] = BedRegion(
                    chrom=regions[-1].chrom,
                    start=regions[-1].start,
                    stop=regions[-1].stop + prom,
                )

        return regions

    def total_len(self) -> int:
        length = 0
        for reg in self.exons:
            length += reg.stop - reg.start + 1
        return length

    def cds_len(self) -> int:
        regions = self.cds_regions()
        length = 0
        for reg in regions:
            length += reg.stop - reg.start + 1
        return length

    def utr3_len(self) -> int:
        utr3 = self.utr3_regions()
        length = 0
        for reg in utr3:
            length += reg.stop - reg.start + 1

        return length

    def utr5_len(self) -> int:
        utr5 = self.utr5_regions()
        length = 0
        for reg in utr5:
            length += reg.stop - reg.start + 1

        return length

    def calc_frames(self) -> list[int]:
        """Calculate codon frames."""
        length = len(self.exons)
        fms = []

        if self.cds[0] > self.cds[1]:
            fms = [-1] * length
        elif self.strand == "+":
            k = 0
            while self.exons[k].stop < self.cds[0]:
                fms.append(-1)
                k += 1
            fms.append(0)
            if self.exons[k].stop < self.cds[1]:
                fms.append((self.exons[k].stop - self.cds[0] + 1) % 3)
                k += 1
            while self.exons[k].stop < self.cds[1] and k < length:
                fms.append(
                    (fms[k] + self.exons[k].stop - self.exons[k].start + 1) % 3,
                )
                k += 1
            fms += [-1] * (length - len(fms))
        else:
            k = length - 1
            while self.exons[k].start > self.cds[1]:
                fms.append(-1)
                k -= 1
            fms.append(0)
            if self.cds[0] < self.exons[k].start:
                fms.append((self.cds[1] - self.exons[k].start + 1) % 3)
                k -= 1
            while self.cds[0] < self.exons[k].start and k > -1:
                fms.append(
                    (fms[-1] + self.exons[k].stop - self.exons[k].start + 1)
                    % 3,
                )
                k -= 1
            fms += [-1] * (length - len(fms))
            fms = fms[::-1]

        assert len(self.exons) == len(fms)
        return fms

    def update_frames(self) -> None:
        """Update codon frames."""
        frames = self.calc_frames()
        for exon, frame in zip(self.exons, frames, strict=True):
            exon.frame = frame

    def test_frames(self) -> bool:
        frames = self.calc_frames()
        for exon, frame in zip(self.exons, frames, strict=True):
            if exon.frame != frame:
                return False
        return True

    def get_exon_number_for(self, start: int, stop: int) -> int:
        for exon_number, exon in enumerate(self.exons):
            if not (start > exon.stop or stop < exon.start):
                return exon_number + 1 if self.strand == "+" \
                       else len(self.exons) - exon_number
        return 0


class GeneModels(
    ResourceConfigValidationMixin,
):
    """Provides class for gene models."""

    def __init__(self, resource: GenomicResource):
        if resource.get_type() != "gene_models":
            raise ValueError(
                f"wrong type of resource passed: {resource.get_type()}")
        self.resource = resource
        self.config = self.validate_and_normalize_schema(
            resource.get_config(), resource,
        )

        self.gene_models: dict[str, list[TranscriptModel]] = defaultdict(list)
        self.utr_models: dict[
                str, dict[tuple[int, int], list[TranscriptModel]]] = \
            defaultdict(lambda: defaultdict(list))
        self.transcript_models: dict[str, Any] = {}
        self.alternative_names: dict[str, Any] = {}

        self.reset()

    @property
    def resource_id(self) -> str:
        return self.resource.resource_id

    def reset(self) -> None:
        self.alternative_names = {}

        self.utr_models = defaultdict(lambda: defaultdict(list))
        self.transcript_models = {}
        self.gene_models = defaultdict(list)

    def add_transcript_model(self, transcript_model: TranscriptModel) -> None:
        """Add a transcript model to the gene models."""
        assert transcript_model.tr_id not in self.transcript_models

        self.transcript_models[transcript_model.tr_id] = transcript_model
        self.gene_models[transcript_model.gene].append(transcript_model)

        self.utr_models[transcript_model.chrom][transcript_model.tx]\
            .append(transcript_model)

    def update_indexes(self) -> None:
        self.gene_models = defaultdict(list)
        self.utr_models = defaultdict(lambda: defaultdict(list))
        for transcript in self.transcript_models.values():
            self.gene_models[transcript.gene].append(transcript)
            self.utr_models[transcript.chrom][transcript.tx].append(transcript)

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

    def gene_models_by_location(
        self, chrom: str, pos1: int,
        pos2: int | None = None,
    ) -> list[TranscriptModel]:
        """Retrieve TranscriptModel objects based on genomic position(s).

        Args:
            chrom (str): The chromosome name.
            pos1 (int): The starting genomic position.
            pos2 (Optional[int]): The ending genomic position. If not provided,
                only models that contain pos1 will be returned.

        Returns:
            list[TranscriptModel]: A list of TranscriptModel objects that
                match the given location criteria.
        """
        result = []

        if pos2 is None:
            key: tuple[int, int]
            for key in self.utr_models[chrom]:
                if key[0] <= pos1 <= key[1]:
                    result.extend(self.utr_models[chrom][key])

        else:
            if pos2 < pos1:
                pos1, pos2 = pos2, pos1

            for key in self.utr_models[chrom]:
                if pos1 <= key[0] <= pos2 or key[0] <= pos1 <= key[1]:
                    result.extend(self.utr_models[chrom][key])

        return result

    def relabel_chromosomes(
        self, relabel: dict[str, str] | None = None,
        map_file: str | None = None,
    ) -> None:
        """Relabel chromosomes in gene model."""
        assert relabel or map_file
        if not relabel:
            assert map_file is not None
            with open(map_file) as infile:
                relabel = cast(
                    dict[str, str],
                    {
                        line.strip("\n\r").split()[:2] for line in infile
                    },
                )

        self.utr_models = {
            relabel[chrom]: v
            for chrom, v in self.utr_models.items()
            if chrom in relabel
        }

        self.transcript_models = {
            tid: tm
            for tid, tm in self.transcript_models.items()
            if tm.chrom in relabel
        }

        for transcript_model in self.transcript_models.values():
            transcript_model.chrom = relabel[transcript_model.chrom]

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
        from .parsing import load_gene_models  # pylint: disable=C0415
        self.reset()
        return load_gene_models(self)

    def is_loaded(self) -> bool:
        return len(self.transcript_models) > 0


def join_gene_models(*gene_models: GeneModels) -> GeneModels:
    """Join muliple gene models into a single gene models object."""
    if len(gene_models) < 2:
        raise ValueError("The function needs at least 2 arguments!")

    gm = GeneModels(gene_models[0].resource)
    gm.utr_models = {}
    gm.gene_models = {}

    gm.transcript_models = gene_models[0].transcript_models.copy()

    for i in gene_models[1:]:
        gm.transcript_models.update(i.transcript_models)

    gm.update_indexes()

    return gm


def build_gene_models_from_file(
    file_name: str,
    file_format: str | None = None,
    gene_mapping_file_name: str | None = None,
) -> GeneModels:
    """Load gene models from local filesystem."""
    config = {
        "type": "gene_models",
        "filename": file_name,
    }
    if file_format:
        config["format"] = file_format
    if gene_mapping_file_name:
        config["gene_mapping"] = gene_mapping_file_name

    res = build_local_resource(".", config)
    return build_gene_models_from_resource(res)


def build_gene_models_from_resource(
    resource: GenomicResource | None,
) -> GeneModels:
    """Load gene models from a genomic resource."""
    if resource is None:
        raise ValueError(f"missing resource {resource}")

    if resource.get_type() != "gene_models":
        logger.error(
            "trying to open a resource %s of type "
            "%s as gene models", resource.resource_id, resource.get_type())
        raise ValueError(f"wrong resource type: {resource.resource_id}")

    return GeneModels(resource)


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
        regions = gene_regions
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
