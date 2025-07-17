from __future__ import annotations

import logging
import pathlib
from collections.abc import Iterable, Sequence
from types import TracebackType

import pysam

from dae.annotation.annotation_config import AttributeInfo
from dae.annotation.format_handlers import stringify
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.pedigrees.families_data import FamiliesData
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariant
from dae.variants_loaders.raw.loader import FullVariant

logger = logging.getLogger(__name__)


class VcfSerializer:
    """Stores a sequence of alleles in a VCF file."""

    def __init__(
        self,
        families: FamiliesData,
        genome: ReferenceGenome,
        output_path: pathlib.Path | str | None,
        header: list[str] | None = None,
        annotations: list[AttributeInfo] | None = None,
    ):
        self.families = families
        self.genome = genome
        self.output_path = output_path
        self._vcf_header = self._build_vcf_header(header)
        self.vcf_file: pysam.VariantFile | None = None
        self.annotations = annotations

    def serialize(
        self,
        full_variants: Iterable[tuple[SummaryVariant, list[FamilyVariant]]],
    ) -> None:
        """Serialize a sequence of alleles to a VCF file."""
        assert self.vcf_file is not None
        for sv, fvs in full_variants:
            record = self._build_vcf_record(sv, fvs)
            self.vcf_file.write(record)

    def serialize_full_variant(self, full_variant: FullVariant) -> None:
        """Serialize a FullVariant to a VCF file."""
        assert self.vcf_file is not None
        record = self._build_vcf_record(full_variant.summary_variant,
                                        full_variant.family_variants)
        self.vcf_file.write(record)

    def _build_vcf_header(
        self, header: list[str] | None,
    ) -> pysam.VariantHeader:
        vcf_header = pysam.VariantHeader()
        if header is not None:
            for line in header:
                vcf_header.add_line(line)
        for contig in self.genome.chromosomes:
            vcf_header.contigs.add(contig)
        for fam in self.families.values():
            for p in fam.members_in_order:
                vcf_header.add_sample(p.sample_id)
        vcf_header.formats.add("GT", 1, "String", "Genotype")

        return vcf_header

    def _build_vcf_file(self) -> pysam.VariantFile:
        output = "-" if self.output_path is None else str(self.output_path)
        return pysam.VariantFile(
            output, "w", header=self._vcf_header,
        )

    def _build_vcf_record(
        self,
        sv: SummaryVariant,
        fvs: Sequence[FamilyVariant],
    ) -> pysam.VariantRecord:
        assert self.vcf_file is not None
        record: pysam.VariantRecord = self.vcf_file.new_record()
        record.contig = sv.chrom
        record.pos = sv.position
        record.ref = sv.reference
        record.alts = tuple(aa.alternative for aa in sv.alt_alleles
                            if aa.alternative is not None)

        svid = [
            f"{aa.chrom}_{aa.position}_{aa.reference}_{aa.alternative}"
            for aa in sv.alt_alleles]
        record.id = ";".join(svid)

        if self.annotations is not None:
            self._update_info(record, sv, self.annotations)

        for fv in fvs:
            fam = self.families[fv.family_id]
            for mem_index, mem in enumerate(fam.members_in_order):
                gt = [g for g in fv.genotype[mem_index] if g > -2]
                record.samples[mem.sample_id]["GT"] = gt
        return record

    def _update_info(
        self,
        vcf_var: pysam.VariantRecord,
        summary_variant: SummaryVariant,
        attributes: list[AttributeInfo],
    ) -> None:
        buffers: list[list] = []
        for attribute in attributes:
            values = summary_variant.get_attribute(attribute.name)
            buff = []
            for value in values:
                if isinstance(value, list):
                    transformed = ";".join(stringify(a, vcf=True)
                                           for a in value)
                elif isinstance(value, dict):
                    transformed = ";".join(
                        f"{k}:{v}"
                        for k, v in value.items()
                    )
                else:
                    transformed = stringify(value, vcf=True)
                transformed = stringify(value, vcf=True) \
                    .replace(";", "|")\
                    .replace(",", "|")\
                    .replace(" ", "_")
                buff.append(transformed)
            buffers.append(buff)
        # If the all values for a given attribute are
        # empty (i.e. - "."), then that attribute has no
        # values to be written and will be skipped in the output
        has_value = {
            attr.name: any(filter(lambda x: x != ".", buffers[idx]))
            for idx, attr in enumerate(attributes)
        }
        for buff, attribute in zip(buffers, attributes, strict=True):
            if attribute.internal or not has_value[attribute.name]:
                continue
            vcf_var.info[attribute.name] = buff

    def __enter__(self) -> VcfSerializer:
        return self.open()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            logger.error(
                "exception while serializing vcf: %s, %s, %s",
                exc_type, exc_value, exc_tb)
        self.close()

    def close(self) -> None:
        if self.vcf_file is not None:
            self.vcf_file.close()
            self.vcf_file = None

    def open(self) -> VcfSerializer:
        self.vcf_file = self._build_vcf_file()
        return self
