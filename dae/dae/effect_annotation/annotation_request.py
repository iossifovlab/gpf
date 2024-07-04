from __future__ import annotations

import abc
import logging

from dae.effect_annotation.gene_codes import NuclearCode
from dae.effect_annotation.variant import Variant
from dae.genomic_resources.gene_models import TranscriptModel
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.utils.regions import BedRegion

logger = logging.getLogger(__name__)


class BaseAnnotationRequest(abc.ABC):
    """Effect annotation request description."""

    def __init__(
        self, reference_genome: ReferenceGenome,
        code: NuclearCode,
        promoter_len: int,
        variant: Variant,
        transcript_model: TranscriptModel,
    ):
        self.reference_genome = reference_genome
        self.code = code
        self.promoter_len = promoter_len
        self.variant = variant
        self.transcript_model = transcript_model
        self.__cds_regions: list[BedRegion] | None = None

    def _clamp_in_cds(self, position: int) -> int:
        if position < self.transcript_model.cds[0]:
            return self.transcript_model.cds[0]  #
        if position > self.transcript_model.cds[1]:
            return self.transcript_model.cds[1]
        return position

    def get_exonic_length(self) -> int:
        start = self.transcript_model.exons[0].start
        end = self.transcript_model.exons[-1].stop
        return self.get_exonic_distance(start, end) + 1

    def get_exonic_position(self) -> int:
        start = self.transcript_model.exons[0].start
        end = self.variant.position
        return self.get_exonic_distance(start, end) + 1

    def get_exonic_distance(self, start: int, end: int) -> int:
        """Calculate exonic distance."""
        length = 0
        for region in self.transcript_model.exons:
            if region.start <= start <= region.stop:
                if region.start <= end <= region.stop:
                    return end - start
                length = region.stop - start + 1
                logger.debug(
                    "start len %d %d-%d", length, start, region.stop,
                )
            else:
                length += region.stop - region.start + 1
                logger.debug(
                    "total %d + len %d %d-%d",
                    length,
                    region.stop - region.start + 1,
                    region.stop,
                    region.start - 1,
                )

            if region.start <= end <= region.stop:
                length -= region.stop - end + 1
                logger.debug(
                    "total %d - len %d %d-%d",
                    length,
                    region.stop - end + 1,
                    region.stop,
                    end - 1,
                )
                break
        return length

    @abc.abstractmethod
    def _get_coding_nucleotide_position(self, position: int) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def get_protein_position(self) -> tuple[int, int]:
        raise NotImplementedError

    def get_protein_position_for_pos(self, position: int) -> int | None:
        if position < self.transcript_model.cds[0]:
            return None
        if position > self.transcript_model.cds[1]:
            return None
        prot_pos = self._get_coding_nucleotide_position(position)
        return prot_pos // 3 + 1

    def _get_sequence(self, start_position: int, end_position: int) -> str:
        logger.debug("_get_sequence %d-%d", start_position, end_position)

        if end_position < start_position:
            return ""

        return self.reference_genome.get_sequence(
            self.transcript_model.chrom, start_position, end_position,
        )

    def cds_regions(self) -> list[BedRegion]:
        if self.__cds_regions is None:
            self.__cds_regions = self.transcript_model.cds_regions()
        return self.__cds_regions

    def get_coding_region_for_pos(self, pos: int) -> int | None:
        """Find conding region for a position."""
        close_match = None
        for i, reg in enumerate(self.transcript_model.exons):
            if reg.start <= pos <= reg.stop:
                return i
            if reg.start - 1 <= pos <= reg.stop + 1:
                close_match = i
        return close_match

    def get_coding_right(self, pos: int, length: int, index: int) -> str:
        """Construct conding sequence to the right of a position."""
        logger.debug(
            "get_coding_right pos:%d len:%d index:%d", pos, length, index,
        )
        if length <= 0:
            return ""

        if index < 0 or pos > self.transcript_model.exons[-1].stop:
            return self.get_codons_right(pos, length)

        reg = self.transcript_model.exons[index]

        if pos == -1:
            pos = reg.start
        last_index = min(pos + length - 1, reg.stop)
        seq = self._get_sequence(pos, last_index)

        length -= len(seq)
        return seq + self.get_coding_right(-1, length, index + 1)

    def get_codons_right(self, pos: int, length: int) -> str:
        """Return coding sequence to the right of a position."""
        if length <= 0:
            return ""

        last_index = pos + length - 1
        seq = self._get_sequence(pos, last_index)

        return seq

    def get_coding_left(self, pos: int, length: int, index: int) -> str:
        """Return coding sequence to the left of a position."""
        logger.debug(
            "get_coding_left pos:%d len:%d index:%d", pos, length, index,
        )
        if length <= 0:
            return ""

        if index < 0 or (
            pos < self.transcript_model.exons[0].start and pos != -1
        ):
            return self.get_codons_left(pos, length)

        reg = self.transcript_model.exons[index]

        if pos == -1:
            pos = reg.stop
        start_index = max(pos - length + 1, reg.start)
        seq = self._get_sequence(start_index, pos)

        length -= len(seq)

        if index == 0:
            return self.get_codons_left(reg.start - 1, length) + seq
        return self.get_coding_left(-1, length, index - 1) + seq

    def get_codons_left(self, pos: int, length: int) -> str:
        if length <= 0:
            return ""
        start_index = pos - length + 1
        seq = self._get_sequence(start_index, pos)
        return seq

    @staticmethod
    def get_nucleotides_count_to_full_codon(length: int) -> int:
        return (3 - (length % 3)) % 3

    def cod2aa(self, codon: str) -> str:
        """Translate codon to amino acid."""
        codon = codon.upper()
        if len(codon) != 3:
            return "?"

        for i in codon:
            if i not in ["A", "C", "T", "G", "N"]:
                print(
                    "Codon can only contain: A, G, C, T, N letters, \
                      this codon is: "
                    + codon,
                )
                return "?"

        for key in self.code.CodonsAaKeys:
            if codon in self.code.CodonsAa[key]:
                return key

        return "?"

    def is_start_codon_affected(self) -> bool:
        return (
            self.variant.position <= self.transcript_model.cds[0] + 2
            and self.transcript_model.cds[0]
            <= self.variant.corrected_ref_position_last
        )

    def is_stop_codon_affected(self) -> bool:
        return (
            self.variant.position <= self.transcript_model.cds[1]
            and self.transcript_model.cds[1] - 2
            <= self.variant.corrected_ref_position_last
        )

    def has_utr3_region(self) -> bool:
        return (
            self.transcript_model.exons[-1].stop
            != self.transcript_model.cds[1]
        )

    def has_utr5_region(self) -> bool:
        return (
            self.transcript_model.exons[0].start
            != self.transcript_model.cds[0]
        )


class PositiveStrandAnnotationRequest(BaseAnnotationRequest):
    """Effect annotation request on the positive strand."""

    def __init__(
        self, reference_genome: ReferenceGenome,
        code: NuclearCode,
        promoter_len: int,
        variant: Variant,
        transcript_model: TranscriptModel,
    ):
        super().__init__(
            reference_genome, code, promoter_len,
            variant, transcript_model)
        self.__amino_acids: tuple[list[str], list[str]] | None = None

    def _get_coding_nucleotide_position(self, position: int) -> int:
        length = 0
        for region in self.cds_regions():
            if region.start - 1 <= position <= region.stop + 1:
                length += position - region.start
                break
            length += region.stop - region.start + 1

        logger.debug(
            "get_coding_nucleotide_position pos=%d len=%d", position, length,
        )
        return length

    def get_protein_position(self) -> tuple[int, int]:
        """Calculate protein position."""
        start_pos = self._clamp_in_cds(self.variant.position)
        end_pos = self._clamp_in_cds(self.variant.ref_position_last - 1)
        end_pos = max(start_pos, end_pos)

        start = self._get_coding_nucleotide_position(start_pos)
        end = self._get_coding_nucleotide_position(end_pos)

        return start // 3 + 1, end // 3 + 1

    def get_protein_length(self) -> int:
        return (
            self._get_coding_nucleotide_position(self.transcript_model.cds[1])
            // 3
        )

    def in_start_codons(self, codon: str) -> bool:
        """Check if request belongs to the start codon."""
        seq = self._get_sequence(
            self.transcript_model.cds[0], self.transcript_model.cds[0] + 2,
        )

        if codon == seq or codon in self.code.startCodons:
            return True
        return False

    def get_frame(self, pos: int, index: int) -> int:
        """Return the frame of the annotation request."""
        reg = self.transcript_model.exons[index]
        if reg.stop < self.transcript_model.cds[0]:
            logger.error(
                "Cannot detect frame. \
                              Start of coding regions is after current region",
            )
            return 0
        start_pos = max(self.transcript_model.cds[0], reg.start)
        assert reg.frame is not None
        frame = (pos - start_pos + reg.frame) % 3
        logger.debug("frame %d for pos=%s", frame, pos)
        return frame

    def get_codons(self) -> tuple[str, str]:
        """Get list of codons."""
        pos = max(self.transcript_model.cds[0], self.variant.position)

        index = self.get_coding_region_for_pos(pos)
        if index is None:
            raise IndexError
        frame = self.get_frame(pos, index)
        assert self.variant.reference is not None
        length = len(self.variant.reference)
        length += self.get_nucleotides_count_to_full_codon(length + frame)

        coding_before_pos = self.get_coding_left(pos - 1, frame, index)
        coding_after_pos = self.get_coding_right(pos, length, index)

        ref_codons = coding_before_pos + coding_after_pos

        assert self.variant.alternate is not None
        length_alt = self.get_nucleotides_count_to_full_codon(
            len(self.variant.alternate) + frame,
        )
        alt_codons = coding_before_pos + self.variant.alternate

        alt_codons += self.get_coding_right(
            self.variant.position + len(self.variant.reference),
            length_alt,
            index,
        )

        logger.debug(
            "ref codons=%s, alt codons=%s", ref_codons, alt_codons,
        )
        return ref_codons, alt_codons

    def get_amino_acids(
        self,
    ) -> tuple[list[str], list[str]]:
        """Construct the list of amino acids."""
        if self.__amino_acids is None:
            ref_codons, alt_codons = self.get_codons()

            ref_amino_acids = [
                self.cod2aa(ref_codons[i: i + 3])
                for i in range(0, len(ref_codons), 3)
            ]

            alt_amino_acids = [
                self.cod2aa(alt_codons[i: i + 3])
                for i in range(0, len(alt_codons), 3)
            ]

            self.__amino_acids = ref_amino_acids, alt_amino_acids
        return self.__amino_acids


class NegativeStrandAnnotationRequest(BaseAnnotationRequest):
    """Effect annotation request on the negative strand."""

    def __init__(
        self, reference_genome: ReferenceGenome,
        code: NuclearCode,
        promoter_len: int,
        variant: Variant,
        transcript_model: TranscriptModel,
    ):
        super().__init__(
            reference_genome, code, promoter_len,
            variant, transcript_model)
        self.__amino_acids: tuple[list[str], list[str]] | None = None

    def _get_coding_nucleotide_position(self, position: int) -> int:
        length = 0
        for region in reversed(self.cds_regions()):
            if region.start - 1 <= position <= region.stop + 1:
                length += region.stop - position
                break
            length += region.stop - region.start + 1

        logger.debug(
            "get_coding_nucleotide_position pos=%d len=%d", position, length,
        )
        return length

    def get_protein_position(self) -> tuple[int, int]:
        """Calculate the protein position."""
        start_pos = self._clamp_in_cds(self.variant.position)
        end_pos = self._clamp_in_cds(self.variant.ref_position_last - 1)
        end_pos = max(start_pos, end_pos)

        end = self._get_coding_nucleotide_position(start_pos)
        start = self._get_coding_nucleotide_position(end_pos)

        return start // 3 + 1, end // 3 + 1

    def get_protein_length(self) -> int:
        return (
            self._get_coding_nucleotide_position(self.transcript_model.cds[0])
            // 3
        )

    def in_start_codons(self, codon: str) -> bool:
        """Check if request belongs to the start codon."""
        seq = self._get_sequence(
            self.transcript_model.cds[1] - 2, self.transcript_model.cds[1],
        )

        complement_codon = self.complement(codon[::-1])
        if codon == seq or complement_codon in self.code.startCodons:
            return True
        return False

    def get_frame(self, pos: int, index: int) -> int:
        """Return the frame of the annotation request."""
        reg = self.transcript_model.exons[index]
        if reg.start > self.transcript_model.cds[1]:
            logger.error(
                "Cannot detect frame. \
                              Start of coding regions is after current region",
            )
            return 0
        stop_pos = min(self.transcript_model.cds[1], reg.stop)
        assert reg.frame is not None
        frame = (stop_pos - pos + reg.frame) % 3
        logger.debug("frame %d for pos=%s", frame, pos)
        return frame

    def get_codons(self) -> tuple[str, str]:
        """Get list of codons."""
        pos = max(self.variant.position, self.transcript_model.cds[0])
        assert self.variant.reference is not None
        last_position = self.variant.position + len(self.variant.reference) - 1

        if pos > last_position + 1:
            return "", ""

        index = self.get_coding_region_for_pos(pos)
        if index is None:
            raise IndexError
        frame = self.get_frame(last_position, index)
        length = last_position - pos + 1
        length += self.get_nucleotides_count_to_full_codon(length + frame)

        logger.debug(
            "last_position=%d, length=%d index=%d pos=%d cds=%d",
            last_position,
            length,
            index,
            self.variant.position,
            self.transcript_model.cds[0],
        )

        coding_before_pos = self.get_coding_left(last_position, length, index)
        coding_after_pos = self.get_coding_right(
            last_position + 1, frame, index,
        )

        logger.debug(
            "coding_before_pos=%s, coding_after_pos=%s frame=%s",
            coding_before_pos,
            coding_after_pos,
            frame,
        )

        ref_codons = coding_before_pos + coding_after_pos

        assert self.variant.alternate is not None
        length_alt = self.get_nucleotides_count_to_full_codon(
            len(self.variant.alternate) + frame,
        )
        alt_codons = self.variant.alternate + coding_after_pos

        alt_codons = (
            self.get_coding_left(self.variant.position - 1, length_alt, index)
            + alt_codons
        )

        logger.debug(
            "%d-%d %d-%d->%d-%d %d-%d",
            last_position,
            last_position - length,
            last_position + 1,
            last_position + 1 + frame,
            pos,
            pos - length_alt,
            last_position + 1,
            last_position + 1 + frame,
        )

        logger.debug(
            "ref codons=%s, alt codons=%s", ref_codons, alt_codons,
        )
        return ref_codons, alt_codons

    @staticmethod
    def complement(sequence: str) -> str:
        """Build the complementary sequence for a sequence of nucleotides."""
        reverse = []
        for nucleotide in sequence.upper():
            if nucleotide == "A":
                reverse.append("T")
            elif nucleotide == "T":
                reverse.append("A")
            elif nucleotide == "G":
                reverse.append("C")
            elif nucleotide == "C":
                reverse.append("G")
            elif nucleotide == "N":
                reverse.append("N")
            else:
                logger.error(
                    "invalid nucleotide: %s in %s",
                    nucleotide, sequence)
        return "".join(reverse)

    def cod2aa(self, codon: str) -> str:
        complement_codon = self.complement(codon[::-1])
        logger.debug(
            "complement codon %s for codon %s", complement_codon, codon,
        )
        return BaseAnnotationRequest.cod2aa(self, complement_codon)

    def get_amino_acids(
        self,
    ) -> tuple[list[str], list[str]]:
        """Construct the list of amino acids."""
        if self.__amino_acids is None:
            ref_codons, alt_codons = self.get_codons()

            ref_amino_acids = [
                self.cod2aa(ref_codons[i - 3: i])
                for i in range(len(ref_codons), 0, -3)
            ]

            alt_amino_acids = [
                self.cod2aa(alt_codons[i - 3: i])
                for i in range(len(alt_codons), 0, -3)
            ]

            self.__amino_acids = ref_amino_acids, alt_amino_acids
        return self.__amino_acids

    def is_start_codon_affected(self) -> bool:
        return BaseAnnotationRequest.is_stop_codon_affected(self)

    def is_stop_codon_affected(self) -> bool:
        return BaseAnnotationRequest.is_start_codon_affected(self)

    def has_utr3_region(self) -> bool:
        return BaseAnnotationRequest.has_utr5_region(self)

    def has_utr5_region(self) -> bool:
        return BaseAnnotationRequest.has_utr3_region(self)


AnnotationRequest = \
    PositiveStrandAnnotationRequest | NegativeStrandAnnotationRequest
