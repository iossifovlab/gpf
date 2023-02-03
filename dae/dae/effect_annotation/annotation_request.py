import logging

logger = logging.getLogger(__name__)


class BaseAnnotationRequest:
    """Effect annotation request description."""

    def __init__(self, annotator, variant, transcript_model):
        self.annotator = annotator
        self.variant = variant
        self.transcript_model = transcript_model
        self.__cds_regions = None
        self.logger = logging.getLogger(__name__)

    def _clamp_in_cds(self, position):
        if position < self.transcript_model.cds[0]:
            return self.transcript_model.cds[0]
        if position > self.transcript_model.cds[1]:
            return self.transcript_model.cds[1]
        return position

    def get_exonic_length(self):
        start = self.transcript_model.exons[0].start
        end = self.transcript_model.exons[-1].stop
        return self.get_exonic_distance(start, end) + 1

    def get_exonic_position(self):
        start = self.transcript_model.exons[0].start
        end = self.variant.position
        return self.get_exonic_distance(start, end) + 1

    def get_exonic_distance(self, start, end):
        """Calculate exonic distance."""
        length = 0
        for region in self.transcript_model.exons:
            if region.start <= start <= region.stop:
                if region.start <= end <= region.stop:
                    return end - start
                length = region.stop - start + 1
            else:
                length += region.stop - region.start + 1

            if region.start <= end <= region.stop:
                length -= region.stop - end + 1
                break
        return length

    def _get_coding_nucleotide_position(self, position):
        raise NotImplementedError()

    def get_protein_position_for_pos(self, position):
        if position < self.transcript_model.cds[0]:
            return None
        if position > self.transcript_model.cds[1]:
            return None
        prot_pos = self._get_coding_nucleotide_position(position)
        return prot_pos // 3 + 1

    def _get_sequence(self, start_position, end_position):
        if end_position < start_position:
            return ""

        return self.annotator.reference_genome.get_sequence(
            self.transcript_model.chrom, start_position, end_position
        )

    def CDS_regions(self):  # pylint: disable=invalid-name
        if self.__cds_regions is None:
            self.__cds_regions = self.transcript_model.CDS_regions()
        return self.__cds_regions

    def get_coding_region_for_pos(self, pos):
        """Find conding region for a position."""
        close_match = None
        for i, reg in enumerate(self.transcript_model.exons):
            if reg.start <= pos <= reg.stop:
                return i
            if reg.start - 1 <= pos <= reg.stop + 1:
                close_match = i
        return close_match

    def get_coding_right(self, pos, length, index):
        """Construct conding sequence to the right of a position."""
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

    def get_codons_right(self, pos, length):
        """Return coding sequence to the right of a position."""
        if length <= 0:
            return ""

        last_index = pos + length - 1
        seq = self._get_sequence(pos, last_index)

        return seq

    def get_coding_left(self, pos, length, index):
        """Return coding sequence to the left of a position."""
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

    def get_codons_left(self, pos, length):
        if length <= 0:
            return ""
        start_index = pos - length + 1
        seq = self._get_sequence(start_index, pos)
        return seq

    @staticmethod
    def get_nucleotides_count_to_full_codon(length):
        return (3 - (length % 3)) % 3

    def cod2aa(self, codon):
        """Translate codon to amino acid."""
        codon = codon.upper()
        if len(codon) != 3:
            return "?"

        for i in codon:
            if i not in ["A", "C", "T", "G", "N"]:
                print(
                    "Codon can only contain: A, G, C, T, N letters, \
                      this codon is: "
                    + codon
                )
                return "?"

        for key in self.annotator.code.CodonsAaKeys:
            if codon in self.annotator.code.CodonsAa[key]:
                return key

        return None

    def is_start_codon_affected(self):
        return (
            self.variant.position <= self.transcript_model.cds[0] + 2
            and self.transcript_model.cds[0]
            <= self.variant.corrected_ref_position_last
        )

    def is_stop_codon_affected(self):
        return (
            self.variant.position <= self.transcript_model.cds[1]
            and self.transcript_model.cds[1] - 2
            <= self.variant.corrected_ref_position_last
        )

    def has_3_UTR_region(self):  # pylint: disable=invalid-name
        return (
            self.transcript_model.exons[-1].stop
            != self.transcript_model.cds[1]
        )

    def has_5_UTR_region(self):  # pylint: disable=invalid-name
        return (
            self.transcript_model.exons[0].start
            != self.transcript_model.cds[0]
        )


class PositiveStrandAnnotationRequest(BaseAnnotationRequest):
    """Effect annotation request on the positive strand."""

    def __init__(self, annotator, variant, transcript_model):
        BaseAnnotationRequest.__init__(
            self, annotator, variant, transcript_model
        )
        self.__amino_acids = None

    def _get_coding_nucleotide_position(self, position):
        length = 0
        for region in self.CDS_regions():
            if region.start - 1 <= position <= region.stop + 1:
                length += position - region.start
                break
            length += region.stop - region.start + 1
        return length

    def get_protein_position(self):
        """Calculate protein position."""
        start_pos = self._clamp_in_cds(self.variant.position)
        end_pos = self._clamp_in_cds(self.variant.ref_position_last - 1)
        end_pos = max(start_pos, end_pos)

        start = self._get_coding_nucleotide_position(start_pos)
        end = self._get_coding_nucleotide_position(end_pos)

        return start // 3 + 1, end // 3 + 1

    def get_protein_length(self):
        return (
            self._get_coding_nucleotide_position(self.transcript_model.cds[1])
            // 3
        )

    def in_start_codons(self, codon):
        """Check if request belongs to the start codon."""
        seq = self._get_sequence(
            self.transcript_model.cds[0], self.transcript_model.cds[0] + 2
        )

        if codon == seq or codon in self.annotator.code.startCodons:
            return True
        return False

    def get_frame(self, pos, index):
        """Return the frame of the annotation request."""
        reg = self.transcript_model.exons[index]
        if reg.stop < self.transcript_model.cds[0]:
            self.logger.error(
                "Cannot detect frame. \
                              Start of coding regions is after current region"
            )
            return 0
        start_pos = max(self.transcript_model.cds[0], reg.start)
        frame = (pos - start_pos + reg.frame) % 3
        return frame

    def get_codons(self):
        """Get list of codons."""
        pos = max(self.transcript_model.cds[0], self.variant.position)

        index = self.get_coding_region_for_pos(pos)
        if index is None:
            raise IndexError
        frame = self.get_frame(pos, index)
        length = len(self.variant.reference)
        length += self.get_nucleotides_count_to_full_codon(length + frame)

        coding_before_pos = self.get_coding_left(pos - 1, frame, index)
        coding_after_pos = self.get_coding_right(pos, length, index)

        ref_codons = coding_before_pos + coding_after_pos

        length_alt = self.get_nucleotides_count_to_full_codon(
            len(self.variant.alternate) + frame
        )
        alt_codons = coding_before_pos + self.variant.alternate

        alt_codons += self.get_coding_right(
            self.variant.position + len(self.variant.reference),
            length_alt,
            index,
        )
        return ref_codons, alt_codons

    def get_amino_acids(self):
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

    def __init__(self, annotator, variant, transcript_model):
        super().__init__(
            annotator, variant, transcript_model)
        self.__amino_acids = None

    def _get_coding_nucleotide_position(self, position):
        length = 0
        for region in reversed(self.CDS_regions()):
            if region.start - 1 <= position <= region.stop + 1:
                length += region.stop - position
                break
            length += region.stop - region.start + 1
        return length

    def get_protein_position(self):
        """Calculate the protein position."""
        start_pos = self._clamp_in_cds(self.variant.position)
        end_pos = self._clamp_in_cds(self.variant.ref_position_last - 1)
        end_pos = max(start_pos, end_pos)

        end = self._get_coding_nucleotide_position(start_pos)
        start = self._get_coding_nucleotide_position(end_pos)

        return start // 3 + 1, end // 3 + 1

    def get_protein_length(self):
        return (
            self._get_coding_nucleotide_position(self.transcript_model.cds[0])
            // 3
        )

    def in_start_codons(self, codon):
        """Check if request belongs to the start codon."""
        seq = self._get_sequence(
            self.transcript_model.cds[1] - 2, self.transcript_model.cds[1]
        )

        complement_codon = self.complement(codon[::-1])
        if codon == seq or complement_codon in self.annotator.code.startCodons:
            return True
        return False

    def get_frame(self, pos, index):
        """Return the frame of the annotation request."""
        reg = self.transcript_model.exons[index]
        if reg.start > self.transcript_model.cds[1]:
            self.logger.error(
                "Cannot detect frame. \
                              Start of coding regions is after current region"
            )
            return 0
        stop_pos = min(self.transcript_model.cds[1], reg.stop)
        frame = (stop_pos - pos + reg.frame) % 3
        return frame

    def get_codons(self):
        """Get list of codons."""
        pos = max(self.variant.position, self.transcript_model.cds[0])
        last_position = self.variant.position + len(self.variant.reference) - 1

        if pos > last_position + 1:
            return "", ""

        index = self.get_coding_region_for_pos(pos)
        if index is None:
            raise IndexError
        frame = self.get_frame(last_position, index)
        length = last_position - pos + 1
        length += self.get_nucleotides_count_to_full_codon(length + frame)

        coding_before_pos = self.get_coding_left(last_position, length, index)
        coding_after_pos = self.get_coding_right(
            last_position + 1, frame, index
        )

        ref_codons = coding_before_pos + coding_after_pos

        length_alt = self.get_nucleotides_count_to_full_codon(
            len(self.variant.alternate) + frame
        )
        alt_codons = self.variant.alternate + coding_after_pos

        alt_codons = (
            self.get_coding_left(self.variant.position - 1, length_alt, index)
            + alt_codons
        )

        return ref_codons, alt_codons

    @staticmethod
    def complement(sequence):
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

    def cod2aa(self, codon):
        complement_codon = self.complement(codon[::-1])
        return BaseAnnotationRequest.cod2aa(self, complement_codon)

    def get_amino_acids(self):
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

    def is_start_codon_affected(self):
        return BaseAnnotationRequest.is_stop_codon_affected(self)

    def is_stop_codon_affected(self):
        return BaseAnnotationRequest.is_start_codon_affected(self)

    def has_3_UTR_region(self):
        return BaseAnnotationRequest.has_5_UTR_region(self)

    def has_5_UTR_region(self):
        return BaseAnnotationRequest.has_3_UTR_region(self)


class AnnotationRequestFactory:
    """Factory for annotation requests."""

    @staticmethod
    def create_annotation_request(annotator, variant, transcript_model):
        if transcript_model.strand == "+":
            return PositiveStrandAnnotationRequest(
                annotator, variant, transcript_model
            )
        return NegativeStrandAnnotationRequest(
            annotator, variant, transcript_model
        )
