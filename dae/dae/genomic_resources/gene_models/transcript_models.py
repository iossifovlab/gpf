from __future__ import annotations

import logging
from typing import Any

from dae.utils.regions import (
    BedRegion,
)

logger = logging.getLogger(__name__)


class Exon:
    """Represent a single exon within a transcript.

    An exon is a segment of a transcript that is retained in the mature RNA
    after splicing. This class stores the genomic coordinates and codon
    reading frame of an exon.

    Attributes:
        start (int): Genomic start position (1-based, inclusive).
        stop (int): Genomic end position (1-based, inclusive).
        frame (int | None): Codon reading frame (0, 1, or 2) for coding
            exons, or None for non-coding exons or UTR regions.

    Example:
        >>> exon = Exon(start=100, stop=200, frame=0)
        >>> print(exon.start, exon.stop)
        100 200
        >>> exon.contains((150, 160))
        True
    """

    __slots__ = ("_frame", "_start", "_stop")

    def __init__(
        self,
        start: int,
        stop: int,
        frame: int | None = None,
    ):
        """Initialize exon model.

        Args:
            start: The genomic start position of the exon (1-based).
            stop (int): The genomic stop position of the exon
                (1-based, closed).
            frame (Optional[int]): The frame of the exon.
        """

        self._start = start
        self._stop = stop
        self._frame = frame

    @property
    def start(self) -> int:
        return self._start

    @property
    def stop(self) -> int:
        return self._stop

    @property
    def frame(self) -> int | None:
        return self._frame

    def __repr__(self) -> str:
        return f"Exon(start={self.start}; stop={self.stop})"

    def contains(self, region: tuple[int, int]) -> bool:
        """Check if this exon fully contains a genomic region.

        Args:
            region (tuple[int, int]): A (start, stop) position tuple to check.

        Returns:
            bool: True if the region is fully contained within this exon.

        Example:
            >>> exon = Exon(100, 200)
            >>> exon.contains((150, 160))
            True
            >>> exon.contains((50, 250))
            False
        """
        start, stop = region
        return self.start <= start and self.stop >= stop


class TranscriptModel:
    """Represent a transcript with all its structural features.

    A transcript model contains complete information about a gene transcript,
    including its genomic location, exon structure, coding regions, and
    additional attributes from the source annotation.

    Attributes:
        gene (str): Gene name/symbol (e.g., "TP53").
        tr_id (str): Transcript identifier, unique within the gene models.
        tr_name (str): Original transcript name from source annotation.
        chrom (str): Chromosome name (e.g., "chr17", "17").
        strand (str): Strand orientation ("+" or "-").
        tx (tuple[int, int]): Transcript start and end positions
            (1-based, closed interval).
        cds (tuple[int, int]): Coding sequence start and end positions
            (1-based, closed interval). For non-coding transcripts,
            cds[0] >= cds[1].
        exons (list[Exon]): List of Exon objects in genomic order.
        attributes (dict[str, Any]): Additional annotation attributes
            (e.g., gene_biotype, gene_version).

    Example:
        >>> from dae.genomic_resources.gene_models.transcript_models import \\
        ...     TranscriptModel, Exon
        >>> tm = TranscriptModel(
        ...     gene="TP53",
        ...     tr_id="ENST00000269305",
        ...     tr_name="TP53-201",
        ...     chrom="17",
        ...     strand="-",
        ...     tx=(7661779, 7687550),
        ...     cds=(7668402, 7687490),
        ...     exons=[Exon(7661779, 7661822), Exon(7668402, 7669690)],
        ...     attributes={"gene_biotype": "protein_coding"},
        ... )
        >>> print(f"Coding: {tm.is_coding()}")
        Coding: True
        >>> regions = tm.cds_regions()
        >>> print(f"CDS has {len(regions)} regions")

    Note:
        - All coordinates use 1-based, closed intervals
        - CDS includes both start and stop codons
        - Exons should be in genomic order (not necessarily 5' to 3')
    """

    def __init__(
        self,
        gene: str,
        tr_id: str,
        tr_name: str,
        chrom: str,
        strand: str, *,
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
        """Check if this transcript is protein-coding.

        Returns:
            bool: True if the transcript has a coding region (CDS),
                False for non-coding transcripts.

        Example:
            >>> if transcript.is_coding():
            ...     cds_len = transcript.cds_len()
            ...     print(f"CDS length: {cds_len}bp")
        """
        return self.cds[0] < self.cds[1]

    def cds_regions(self, ss_extend: int = 0) -> list[BedRegion]:
        """Compute coding sequence (CDS) regions.

        Extracts the portions of exons that contain coding sequence,
        optionally extending into splice sites.

        Args:
            ss_extend (int): Number of bases to extend into splice sites
                at exon boundaries. Default is 0 (no extension).

        Returns:
            list[BedRegion]: List of BedRegion objects representing CDS
                segments. Returns empty list for non-coding transcripts.

        Example:
            >>> cds_regions = transcript.cds_regions()
            >>> for region in cds_regions:
            ...     print(f"{region.chrom}:{region.start}-{region.stop}")
            >>> # With splice site extension
            >>> extended = transcript.cds_regions(ss_extend=3)

        Note:
            CDS regions include both start and stop codons. Use
            collect_gtf_cds_regions() from serialization module to
            exclude the stop codon for GTF format.
        """
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
        """Get 5' untranslated region (5' UTR) segments.

        The 5' UTR extends from the transcription start to the start codon
        (translation start). Strand orientation is considered.

        Returns:
            list[BedRegion]: List of 5' UTR regions. Returns empty list for
                non-coding transcripts.

        Example:
            >>> utr5 = transcript.utr5_regions()
            >>> utr5_length = sum(r.stop - r.start + 1 for r in utr5)
            >>> print(f"5' UTR: {utr5_length}bp")

        Note:
            For positive strand: regions before CDS start.
            For negative strand: regions after CDS end.
        """
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
            while self.exons[k].stop < self.cds[1] and k < len(self.exons):
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
        """Get 3' untranslated region (3' UTR) segments.

        The 3' UTR extends from the stop codon (translation end) to the
        transcription end. Strand orientation is considered.

        Returns:
            list[BedRegion]: List of 3' UTR regions. Returns empty list for
                non-coding transcripts.

        Example:
            >>> utr3 = transcript.utr3_regions()
            >>> utr3_length = sum(r.stop - r.start + 1 for r in utr3)
            >>> print(f"3' UTR: {utr3_length}bp")

        Note:
            For positive strand: regions after CDS end.
            For negative strand: regions before CDS start.
        """
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
        """Get all transcript regions with optional extensions.

        Returns all exonic regions, optionally extending into splice sites
        and promoter regions.

        Args:
            ss_extend (int): Number of bases to extend into splice sites
                at coding exon boundaries. Default is 0.
            prom (int): Number of bases to extend into promoter region
                upstream of transcription start. Default is 0.

        Returns:
            list[BedRegion]: List of all transcript regions, potentially
                extended based on parameters.

        Example:
            >>> # Basic exonic regions
            >>> regions = transcript.all_regions()
            >>> # With splice site extension
            >>> regions = transcript.all_regions(ss_extend=3)
            >>> # With promoter region
            >>> regions = transcript.all_regions(prom=2000)

        Note:
            Promoter extension is strand-aware: extends upstream of the
            transcription start (before first exon for +, after last for -).
        """
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
                            chrom=self.chrom,
                            start=exon.start, stop=exon.stop),
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
        """Calculate reading frame for each exon.

        Computes the codon reading frame (0, 1, or 2) for each exon based
        on the CDS coordinates and strand orientation.

        Returns:
            list[int]: Reading frame for each exon. Values are:
                - 0, 1, or 2 for coding exons (bases into current codon)
                - -1 for non-coding exons or non-coding transcripts

        Example:
            >>> frames = transcript.calc_frames()
            >>> for exon, frame in zip(transcript.exons, frames):
            ...     if frame >= 0:
            ...         print(f"Exon {exon.start}-{exon.stop}: frame {frame}")

        Note:
            Frame calculation is strand-aware and considers exon order.
            Use update_frames() to set frame attribute on Exon objects.
        """
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
                    (fms[k] +
                     self.exons[k].stop - self.exons[k].start + 1) % 3,
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
        """Update the frame attribute of all exons.

        Calculates reading frames using calc_frames() and updates the
        frame attribute of each Exon object.

        Example:
            >>> transcript.update_frames()
            >>> for exon in transcript.exons:
            ...     print(f"Exon frame: {exon.frame}")

        Note:
            This modifies the Exon objects in place.
        """
        frames = self.calc_frames()
        for exon, frame in zip(self.exons, frames, strict=True):
            exon._frame = frame  # noqa: SLF001

    def test_frames(self) -> bool:
        """Verify that exon frames are correctly set.

        Compares the frame attribute of each exon with the calculated
        frame to ensure consistency.

        Returns:
            bool: True if all exon frames match calculated values,
                False otherwise.

        Example:
            >>> transcript.update_frames()
            >>> assert transcript.test_frames()
        """
        frames = self.calc_frames()
        for exon, frame in zip(self.exons, frames, strict=True):
            if exon.frame != frame:
                return False
        return True
