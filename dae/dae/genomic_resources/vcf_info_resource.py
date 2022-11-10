from __future__ import annotations

import logging
from functools import cache
from typing import Dict, Any, Union, List, Generator

from dae.genomic_resources.repository import GenomicResource
from dae.genomic_resources.genomic_scores import ScoreDef, ScoreValue


logger = logging.getLogger(__name__)


class VcfInfoResource:
    """Class that handles reading VCF INFO field."""

    VCF_TYPE_CONVERSION_MAP = {
        "Integer": "int",
        "Float": "float",
        "String": "str",
        "Flag": "bool",
    }

    def __init__(self, resource: GenomicResource):
        assert resource.get_type() == "vcf_info"
        self.resource = resource
        self.config = self.resource.get_config()

        self.vcf = None

    def _format_info(self, info):
        """Format variant info output according to types present in header."""
        for header in self.get_header_info().values():
            if header["type"] not in self.VCF_TYPE_CONVERSION_MAP:
                continue
            convert = self.VCF_TYPE_CONVERSION_MAP[header["type"]]

            if header["Number"] != 1:
                for key, value in info.items():
                    info[key] = convert(value)
            else:
                info[key] = convert(value)

    def get_config(self):
        return self.config

    @cache
    def score_id(self):
        return self.get_config().get("id")

    def get_score_config(self, score_id):
        return self.get_header_info().get(score_id)

    @cache
    def get_header_info(self) -> Dict[str, Dict[str, Union[str, int]]]:
        """Return dictionary of VCF INFO field description."""
        if not self.is_open():
            raise ValueError("trying to work with closed VcfInfoResource")
        assert self.vcf is not None

        output = {}
        for attribute_name, metadata in self.vcf.header.info.items():
            if metadata.number == "A":
                def value_parser(v):
                    logger.warning(
                        "unable to handle list of score values; "
                        "using one value only")
                    return v[0]
            elif metadata.number == ".":
                def value_parser(v):
                    logger.warning(
                        "unable to handle list of score values; "
                        "using one value only")
                    return v[0] if v is not None else None
            elif metadata.number == "R":
                def value_parser(v):
                    logger.warning(
                        "unable to handle list of score values; "
                        "using one value only")
                    return v[1]
            else:
                number = int(metadata.number)
                if number > 1:
                    def value_parser(v):
                        logger.warning(
                            "unable to handle list of score values; "
                            "using one value only")
                        return v[0]
                else:
                    def value_parser(v):
                        return v

            output[attribute_name] = ScoreDef(
                attribute_name,
                metadata.description,
                None,  # col_index
                self.VCF_TYPE_CONVERSION_MAP[metadata.type],
                value_parser,  # value_parser
                None,  # na_values
                None,  # pos_aggregator
                None,  # nuc_aggregator
                metadata.description,
            )
        return output

    def open(self) -> VcfInfoResource:
        if self.is_open():
            return self
        config = self.resource.get_config()
        self.vcf = self.resource.open_vcf_file(
            config["filename"], config["index_filename"])
        return self

    def is_open(self):
        return self.vcf is not None

    def close(self):
        self.vcf.close()
        self.vcf = None

    @cache
    def get_all_chromosomes(self):
        if not self.is_open():
            raise ValueError("trying to work with closed VcfInfoResource")
        return list(self.vcf.header.contigs)

    @cache
    def get_all_scores(self):
        if not self.is_open():
            raise ValueError("trying to work with closed VcfInfoResource")
        return list(self.get_header_info().values())

    def get_variant_info(self, chrom: str, pos: int) -> Dict[str, Any]:
        """Return dictionary of VCF INFO field data for given variant."""
        if not self.is_open():
            raise ValueError("trying to work with closed VcfInfoResource")
        assert self.vcf is not None

        start = pos - 1
        end = pos
        try:
            record = next(self.vcf.fetch(contig=chrom, start=start, end=end))
        except StopIteration:
            record = None
        output = {}
        if record is not None:
            for attribute_name, value in record.info.items():
                output[attribute_name] = value
        return output

    def fetch_region(self, chrom: str, pos_begin: int, pos_end: int,
                     scores: List[str]) \
            -> Generator[dict[str, ScoreValue], None, None]:
        """Return score values in a region."""
        if not self.is_open():
            raise ValueError(
                f"trying to work with closed "
                f"VcfInfoResource({self.score_id()})")
        assert self.vcf is not None

        requested_scores = scores if scores else self.get_all_scores()
        requested_score_defs = [
            self.get_header_info()[score_id] for score_id in requested_scores]
        for vcf_record in self.vcf.fetch(
                contig=chrom, start=pos_begin - 1, end=pos_end):
            assert len(vcf_record.alts) == 1
            result = {}
            for score_def in requested_score_defs:
                value = score_def.value_parser(
                    vcf_record.info.get(score_def.score_id))
                result[score_def.score_id] = value
            yield result

    def fetch_scores(
            self, chrom: str, position: int, reference: str, alternative: str,
            scores: List[str] = None):
        """Fetch scores values for specific allele."""
        if not self.is_open():
            raise ValueError(
                f"trying to work with closed "
                f"VcfInfoResource({self.score_id()})")
        assert self.vcf is not None

        if chrom not in self.get_all_chromosomes():
            raise ValueError(
                f"{chrom} is not among the available chromosomes for "
                f"VCF Info resource {self.score_id()}")

        # lines = list(self._fetch_lines(chrom, position, position))
        vcf_records = list(self.vcf.fetch(chrom, position - 1, position))
        if not vcf_records:
            return None

        selected_vcf = None
        selected_alt = None
        for vcf_record in vcf_records:
            assert len(vcf_record.alts) == 1
            for alt_index, alt in enumerate(vcf_record.alts):
                if vcf_record.ref == reference and alt == alternative:
                    selected_vcf = vcf_record
                    selected_alt = alt_index
                    break

        if selected_vcf is None:
            return None
        assert selected_alt == 0

        requested_scores = scores if scores else self.get_all_scores()
        requested_score_defs = [
            self.get_header_info()[score_id] for score_id in requested_scores
        ]
        return {
            score_def.score_id: score_def.value_parser(
                selected_vcf.info.get(score_def.score_id))
            for score_def in requested_score_defs}
