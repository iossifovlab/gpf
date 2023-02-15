"""Defines reference genome class."""
from __future__ import annotations

import os
import logging
import copy
import textwrap

from typing import Optional, Any, cast

from jinja2 import Template
from markdown2 import markdown
from cerberus import Validator

from dae.genomic_resources.fsspec_protocol import build_local_resource
from dae.genomic_resources.resource_implementation import \
    GenomicResourceImplementation, get_base_resource_schema

from dae.utils.regions import Region
from dae.genomic_resources import GenomicResource


logger = logging.getLogger(__name__)


class ReferenceGenome(GenomicResourceImplementation):
    """Provides an interface for quering a reference genome."""

    config_validator = Validator

    def __init__(self, resource: GenomicResource):
        super().__init__(resource)
        if resource.get_type() != "genome":
            raise ValueError(
                f"wront type of resource passed: {resource.get_type()}")
        self._index: dict[str, Any] = {}
        self._chromosomes: list[str] = []
        self._sequence = None

        self.pars: dict = self._parse_pars(resource.get_config())

    @property
    def resource_id(self):
        return self.resource.resource_id

    @staticmethod
    def _parse_pars(config) -> dict:
        if "PARS" not in config:
            return {}

        assert config["PARS"]["X"] is not None
        regions_x = [
            Region.from_str(region) for region in config["PARS"]["X"]
        ]
        chrom_x = regions_x[0].chrom

        result = {
            chrom_x: regions_x
        }

        if config["PARS"]["Y"] is not None:
            regions_y = [
                Region.from_str(region) for region in config["PARS"]["Y"]
            ]
            chrom_y = regions_y[0].chrom
            result[chrom_y] = regions_y
        return result

    @property
    def chromosomes(self) -> list[str]:
        """Return a list of all chromosomes of the reference genome."""
        return self._chromosomes

    def _load_genome_index(self, index_content):
        for line in index_content.split("\n"):
            line = line.strip()
            if not line:
                break
            line = line.split()

            self._index[line[0]] = {
                "length": int(line[1]),
                "startBit": int(line[2]),
                "seqLineLength": int(line[3]),
                "lineLength": int(line[4]),
            }
        self._chromosomes = list(self._index.keys())

    @property
    def files(self):
        config = self.resource.get_config()
        file_name = config["filename"]
        index_file_name = config.get("index_file", f"{file_name}.fai")
        return {file_name, index_file_name}

    def close(self):
        """Close reference genome sequence file-like objects."""
        # FIXME: consider using weakref to work around this problem
        # self._sequence.close()
        # self._sequence = None

        # self._index = {}
        # self._chromosomes = []

    def open(self) -> ReferenceGenome:
        """Open reference genome resources."""
        if self.is_open():
            logger.info(
                "opening already opened reference genome %s",
                self.resource.resource_id)
            return self

        config = self.resource.get_config()
        file_name = config["filename"]
        index_file_name = config.get(
            "index_file", f"{file_name}.fai")

        index_content = self.resource.get_file_content(index_file_name)
        self._load_genome_index(index_content)
        self._sequence = self.resource.open_raw_file(
            file_name, "rb", uncompress=False, seekable=True)

        return self

    def is_open(self):
        return self._sequence is not None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type is not None:
            logger.error(
                "exception while using reference genome: %s, %s, %s",
                exc_type, exc_value, exc_tb, exc_info=True)
        try:
            self.close()
        except Exception:  # pylint: disable=broad-except
            logger.error(
                "exception during closing reference genome", exc_info=True)

    def get_chrom_length(self, chrom: str) -> int:
        """Return the length of a specified chromosome."""
        chrom_data = self._index.get(chrom)
        if chrom_data is None:
            raise ValueError(f"can't fined chromosome {chrom}")
        return cast(int, chrom_data["length"])

    def get_all_chrom_lengths(self):
        """Return list of all chromosomes lengths."""
        return [
            (key, value["length"])
            for key, value in self._index.items()]

    def get_sequence(self, chrom, start, stop):
        """Return sequence of nucleotides from specified chromosome region."""
        if chrom not in self.chromosomes:
            logger.warning(
                "chromosome %s not found in %s",
                chrom, self.resource.resource_id)
            return None

        self._sequence.seek(
            self._index[chrom]["startBit"]
            + start
            - 1
            + (start - 1) // self._index[chrom]["seqLineLength"]
        )

        length = stop - start + 1
        line_feeds = 1 + length // self._index[chrom]["seqLineLength"]

        sequence = self._sequence.read(length + line_feeds).decode("ascii")
        sequence = sequence.replace("\n", "")[:length]
        return sequence.upper()

    def is_pseudoautosomal(self, chrom: str, pos: int) -> bool:
        """Return true if specified position is pseudoautosomal."""
        def in_any_region(
                chrom: str, pos: int, regions: list[Region]) -> bool:
            return any(map(lambda reg: reg.isin(chrom, pos), regions))

        pars_regions = self.pars.get(chrom, None)
        if pars_regions:
            return in_any_region(
                chrom, pos, pars_regions  # type: ignore
            )
        return False

    @staticmethod
    def get_template():
        return Template(textwrap.dedent("""
            {% extends base %}
            {% block content %}
            <hr>
            <h3>Genome file:</h3>
            <a href="{{ data["filename"] }}">
            {{ data["filename"] }}
            </a>
            {% if data["chrom_prefix"] %}
            <p>chrom prefix: {{ data["chrom_prefix"] }}</p>
            {% endif %}
            {% if data["PARS"] %}
            <h3>Pseudoautosomal regions:</h6>
            {% if data["PARS"]["X"] %}
            <p>X chromosome:</p>
            <ul>
            {% for region in data["PARS"]["X"] %}
            <li>{{region}}</li>
            {% endfor %}
            </ul>
            {% endif %}

            {% if data["PARS"]["Y"] %}
            <p>Y chromosome: </p>
            <ul>
            {% for region in data["PARS"]["Y"] %}
            <li>{{region}}</li>
            {% endfor %}
            </ul>
            {% endif %}

            {% endif %}
            {% endblock %}
        """))

    def get_info(self):
        info = copy.deepcopy(self.config)
        if "meta" in info:
            info["meta"] = markdown(info["meta"])
        return info

    @staticmethod
    def get_schema():
        return {
            **get_base_resource_schema(),
            "filename": {"type": "string"},
            "chrom_prefix": {"type": "string"},
            "PARS": {"type": "dict", "schema": {
                "X": {"type": "list", "schema": {"type": "string"}},
                "Y": {"type": "list", "schema": {"type": "string"}},
            }}
        }


def build_reference_genome_from_file(filename) -> ReferenceGenome:
    """Open a reference genome from a file."""
    dirname = os.path.dirname(filename)
    basename = os.path.basename(filename)
    res = build_local_resource(dirname, {
        "type": "genome",
        "filename": basename,
    })
    return build_reference_genome_from_resource(res)


def build_reference_genome_from_resource(
        resource: Optional[GenomicResource]) -> ReferenceGenome:
    """Open a reference genome from resource."""
    if resource is None:
        raise ValueError("None resource passed")

    if resource.get_type() != "genome":
        logger.error(
            "trying to open a resource %s of type "
            "%s as reference genome",
            resource.resource_id, resource.get_type())
        raise ValueError(f"wrong resource type: {resource.resource_id}")

    ref = ReferenceGenome(resource)
    return ref
