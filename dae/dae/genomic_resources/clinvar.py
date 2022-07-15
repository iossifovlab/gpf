"""Module containing class for reading ClinVar VCF files from resource."""
import logging
from functools import cache
from typing import Dict, Any, Union
from dae.genomic_resources.repository import GenomicResource

logger = logging.getLogger(__name__)


class ClinVarVcf:
    """Class that handles reading ClinVar's release VCF files."""

    VCF_TYPE_CONVERSION_MAP = {
        "Integer": int,
        "Float": float
    }

    def __init__(self, resource: GenomicResource):
        assert resource.get_type() == "clinvar_resource"
        self.resource = resource
        config = resource.get_config()
        self.vcf = self._load_vcf(config["filename"], config["index_filename"])

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

    def _load_vcf(self, filename: str, index_filename: str):
        return self.resource.open_vcf_file(filename, index_filename)

    @cache
    def get_header_info(self) -> Dict[str, Dict[str, Union[str, int]]]:
        """Return dictionary of ClinVar info description."""
        assert not self.vcf.closed
        output = {}
        for attribute_name, metadata in self.vcf.header.info.items():
            output[attribute_name] = {
                "name": attribute_name,
                "type": metadata.type,
                "number": metadata.number,
                "description": metadata.description
            }
        return output

    def get_variant_info(self, chrom: str, pos: int) -> Dict[str, Any]:
        """Return dictionary of ClinVar info for given variant."""
        assert not self.vcf.closed
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

    def close(self):
        self.vcf.close()
