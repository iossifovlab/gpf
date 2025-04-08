from __future__ import annotations

import logging
import textwrap
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import numpy as np
import tensorflow as tf
from pkg_resources import resource_filename

from dae.annotation.annotatable import Annotatable, VCFAllele
from dae.annotation.annotation_config import (
    AnnotationConfigParser,
    AnnotatorInfo,
    AttributeInfo,
)
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    Annotator,
)
from dae.annotation.annotator_base import AnnotatorBase
from dae.genomic_resources.aggregators import (
    Aggregator,
    build_aggregator,
)
from dae.genomic_resources.gene_models import (
    GeneModels,
    build_gene_models_from_resource,
)
from dae.genomic_resources.genomic_context import get_genomic_context
from dae.genomic_resources.reference_genome import (
    ReferenceGenome,
    build_reference_genome_from_resource_id,
)
from spliceai_annotator.utils import one_hot_encode

logger = logging.getLogger(__name__)


def build_spliceai_annotator(
    pipeline: AnnotationPipeline,
    info: AnnotatorInfo,
) -> Annotator:
    return SpliceAIAnnotator(pipeline, info)


@dataclass
class _AttrConfig:
    """SpliceAI attributes definition class."""

    name: str
    value_type: str
    description: str
    aggregator: str


@dataclass
class _AttrDef:
    """SpliceAI attributes definition class."""

    name: str
    documentation: str
    aggregator: Aggregator


class SpliceAIAnnotator(AnnotatorBase):
    """SpliceAI annotator class."""

    def __init__(
        self,
        pipeline: AnnotationPipeline,
        info: AnnotatorInfo,
    ):
        gene_models_resource_id = info.parameters.get("gene_models")
        if gene_models_resource_id is None:
            gene_models = get_genomic_context().get_gene_models()
            if gene_models is None:
                raise ValueError(f"Can't create {info.type}: "
                                 "gene model resource are missing in config "
                                 "and context")
        else:
            resource = pipeline.repository.get_resource(
                gene_models_resource_id)
            gene_models = build_gene_models_from_resource(resource)
        assert isinstance(gene_models, GeneModels)

        genome_resource_id = info.parameters.get("genome") or \
            gene_models.reference_genome_id or \
            (pipeline.preamble.input_reference_genome
             if pipeline.preamble is not None else None)
        if genome_resource_id is None:
            genome = get_genomic_context().get_reference_genome()
            if genome is None:
                raise ValueError(f"The {info} has no reference genome"
                                  " specified and no genome was found"
                                  " in the gene models' configuration,"
                                  " the context or the annotation config's"
                                  " preamble.")
        else:
            genome = build_reference_genome_from_resource_id(
                genome_resource_id, pipeline.repository)
        assert isinstance(genome, ReferenceGenome)


        info.documentation += textwrap.dedent("""

SpliceAI Annotator plugin uses 
<a href="https://www.cell.com/cell/fulltext/S0092-8674(18)31629-5">SpliceAI</a>
models to predict splice site variant effects.

""")  # noqa
        info.resources += [genome.resource, gene_models.resource]
        if not info.attributes:
            info.attributes = AnnotationConfigParser.parse_raw_attributes([
                "gene",
                "transcript_ids",
                "DS_AG",
                "DS_AL",
                "DS_DG",
                "DS_DL",
                "DS_MAX",
            ])

        super().__init__(pipeline, info, {
            name: (attr.value_type, attr.description)
            for name, attr in self._attributes_definition().items()
        })
        self.used_attributes = [
            attr.source for attr in self.get_info().attributes
        ]
        self._attribute_defs = self._collect_attributes_definitions(
            self.get_info().attributes,
        )

        self.genome = genome
        self.gene_models = gene_models
        self._distance = int(info.parameters.get("distance", 50))
        if self._distance < 0 or self._distance > 5000:
            logger.warning(
                "distance %s is out of range. "
                "Setting it to 50.", self._distance,
            )
            self._distance = 50
        self._mask = int(info.parameters.get("mask", 0))
        if self._mask not in [0, 1]:
            logger.warning(
                "mask %s is out of range. "
                "Setting it to 0.", self._mask,
            )
            self._mask = 0
        self._models = None

    def _attributes_definition(self) -> dict[str, _AttrConfig]:
        return {
            "gene": _AttrConfig(
                "gene",
                "str",
                "Gene symbol",
                "join(,)",
            ),
            "transcript_ids": _AttrConfig(
                "transcript_ids",
                "str",
                "Transcript IDs",
                "join(,)",
            ),
            "DS_AG": _AttrConfig(
                "DS_AG",
                "float",
                "Delta score for acceptor gain",
                "max",
            ),
            "DS_AL": _AttrConfig(
                "DS_AL",
                "float",
                "Delta score for acceptor loss",
                "max",
            ),
            "DS_DG": _AttrConfig(
                "DS_DG",
                "float",
                "Delta score for donor gain",
                "max",
            ),
            "DS_DL": _AttrConfig(
                "DS_DL",
                "float",
                "Delta score for donor loss",
                "max",
            ),
            "DS_MAX": _AttrConfig(
                "DS_MAX",
                "float",
                "Maximum delta score",
                "max",
            ),
            "DP_AG": _AttrConfig(
                "DP_AG",
                "int",
                "Delta position for acceptor gain",
                "join(;)",
            ),
            "DP_AL": _AttrConfig(
                "DP_AL",
                "int",
                "Delta position for acceptor loss",
                "join(;)",
            ),
            "DP_DG": _AttrConfig(
                "DP_DG",
                "int",
                "Delta position for donor gain",
                "join(;)",
            ),
            "DP_DL": _AttrConfig(
                "DP_DL",
                "int",
                "Delta position for donor loss",
                "join(;)",
            ),
            "ref_A_p": _AttrConfig(
                "ref_A_p",
                "str",
                "Reference acceptor probabilities",
                "join(;)",
            ),
            "ref_D_p": _AttrConfig(
                "ref_D_p",
                "str",
                "Reference donor probabilities",
                "join(;)",
            ),
            "alt_A_p": _AttrConfig(
                "alt_A_p",
                "str",
                "Alternative acceptor probabilities",
                "join(;)",
            ),
            "alt_D_p": _AttrConfig(
                "alt_D_p",
                "str",
                "Alternative donor probabilities",
                "join(;)",
            ),
            "delta_score": _AttrConfig(
                "delta_score",
                "str",
                "Delta score calculated using SpliceAI models."
                "These include delta scores (DS) and "
                "delta positions (DP) for acceptor gain (AG), "
                "acceptor loss (AL), "
                "donor gain (DG), and donor loss (DL). "
                "<br/>Format: <em>"
                "ALLELE|SYMBOL|DS\\_AG|DS\\_AL|DS\\_DG|DS\\_DL|"
                "DP\\_AG|DP\\_AL|DP\\_DG|DP\\_DL"
                "</em>",
                "join(;)",
            ),
        }

    def _collect_attributes_definitions(
        self,
        attributes: list[AttributeInfo],
    ) -> list[_AttrDef]:
        """Collect attributes configuration."""
        result = []
        for attr in attributes:
            if attr.name not in self._attributes_definition():
                logger.error(
                    "Attribute %s is not supported by SpliceAI annotator",
                    attr.name,
                )
                continue

            attr_config = self._attributes_definition()[attr.name]
            aggregator = attr.parameters.get("aggregator")
            if aggregator is not None:
                documenation = (
                    f"{attr_config.description}\n"
                    f"Aggregator: {aggregator}"
                )
            else:
                aggregator = attr_config.aggregator
                documenation = (
                    f"{attr_config.description}\n\n"
                    f"Aggregator (<em>default</em>): {aggregator}"
                )
            attr._documentation = documenation  # noqa: SLF001
            result.append(_AttrDef(
                attr.name,
                documenation,
                build_aggregator(aggregator),
            ))
        return result

    def close(self) -> None:
        self.genome.close()
        super().close()

    def open(self) -> Annotator:
        self.genome.open()
        self.gene_models.load()
        model_paths = [
            f"models/spliceai{i}.h5" for i in range(1, 6)
        ]
        self._models = [
            tf.keras.models.load_model(resource_filename(__name__, path))
            for path in model_paths
        ]
        return super().open()

    def _not_found(self) -> dict[str, Any]:
        return {
            "gene": None,
            "transcript_ids": None,
            "DS_AG": None,
            "DS_AL": None,
            "DS_DG": None,
            "DS_DL": None,
            "DS_MAX": None,
            "DP_AG": None,
            "DP_AL": None,
            "DP_DG": None,
            "DP_DL": None,
            "ref_A_p": None,
            "ref_D_p": None,
            "alt_A_p": None,
            "alt_D_p": None,
            "delta_score": None,
        }

    def _width(self) -> int:
        return 10000 + 2 * self._distance + 1

    def _is_valid_annotatable(
        self, annotatable: Annotatable,
    ) -> bool:
        if annotatable is None:
            return False
        if not isinstance(annotatable, VCFAllele):
            return False
        if any(c in {".", "-", "*", ">", "<"} for c in annotatable.alt):
            logger.warning(
                "Skipping record (strange alt): %s", annotatable,
            )
            return False

        if len(annotatable.ref) > 2 * self._distance:
            logger.warning(
                "Skipping record (ref too long): %s", annotatable,
            )
            return False
        if len(annotatable.ref) > 1 and len(annotatable.alt) > 1:
            logger.warning(
                "Skipping record (complex VCFAllele): %s", annotatable,
            )
            return False

        return True

    def _do_annotate(
        self, annotatable: Annotatable,
        context: dict[str, Any],  # noqa: ARG002
    ) -> dict[str, Any]:
        logger.debug(
            "processing annotatable %s", annotatable)

        if not self._is_valid_annotatable(annotatable):
            return self._not_found()
        assert not (len(annotatable.ref) > 1 and len(annotatable.alt) > 1)

        transcripts = self.gene_models.gene_models_by_location(
            annotatable.chromosome,
            annotatable.pos,
        )
        if not transcripts:
            return self._not_found()

        width = self._width()
        seq = self.genome.get_sequence(
            annotatable.chromosome,
            annotatable.pos - width // 2,
            annotatable.pos + width // 2,
        )
        if len(seq) != width:
            logger.warning(
                "Skipping record (near chromosome end): %s", annotatable,
            )
            return self._not_found()
        ref_len = len(annotatable.ref)
        if seq[width // 2: width // 2 + ref_len] != annotatable.ref:
            logger.warning(
                "Skipping record (wrong reference): %s", annotatable,
            )
            return self._not_found()

        genes = defaultdict(list)
        for transcript in transcripts:
            genes[transcript.gene].append(transcript)

        results = defaultdict(list)
        for gene, transcripts in genes.items():
            tx = (
                min(t.tx[0] for t in transcripts),
                max(t.tx[1] for t in transcripts),
            )
            strands = [t.strand for t in transcripts]
            if not all(s == strands[0] for s in strands):
                logger.warning(
                    "Skipping record (mixed strands): %s", annotatable,
                )
                return self._not_found()
            strand = strands[0]

            xref, xalt = self._seq_padding(
                seq, tx, annotatable,
            )

            y = self._predict(
                xref, xalt, strand,
                annotatable,
            )

            idx_pa = (y[1, :, 1] - y[0, :, 1]).argmax()
            idx_na = (y[0, :, 1] - y[1, :, 1]).argmax()
            idx_pd = (y[1, :, 2] - y[0, :, 2]).argmax()
            idx_nd = (y[0, :, 2] - y[1, :, 2]).argmax()

            pa = (y[1, idx_pa, 1] - y[0, idx_pa, 1])
            na = (y[0, idx_na, 1] - y[1, idx_na, 1])
            pd = (y[1, idx_pd, 2] - y[0, idx_pd, 2])
            nd = (y[0, idx_nd, 2] - y[1, idx_nd, 2])

            results["gene"].append(gene)
            results["transcript_ids"].append(
                ",".join([t.tr_id for t in transcripts]),
            )
            results["DS_AG"].append(pa)
            results["DS_AL"].append(na)
            results["DS_DG"].append(pd)
            results["DS_DL"].append(nd)
            results["DS_MAX"].append(max(pa, na, pd, nd))
            results["DP_AG"].append(idx_pa - self._distance)
            results["DP_AL"].append(idx_na - self._distance)
            results["DP_DG"].append(idx_pd - self._distance)
            results["DP_DL"].append(idx_nd - self._distance)

            results["ref_A_p"].append(
                ",".join(
                    [f"{p:.4f}" for p in y[0, :, 1]],
                ))
            results["ref_D_p"].append(
                ",".join(
                    [f"{p:.4f}" for p in y[0, :, 2]],
                ))
            results["alt_A_p"].append(
                ",".join(
                    [f"{p:.4f}" for p in y[1, :, 1]],
                ))
            results["alt_D_p"].append(
                ",".join(
                    [f"{p:.4f}" for p in y[1, :, 2]],
                ))

            results["delta_score"].append(
                f"{annotatable.alt}|{gene}|"
                f"{pa:.2f}|{na:.2f}|"
                f"{pd:.2f}|{nd:.2f}|"
                f"{idx_pa - self._distance}|"
                f"{idx_na - self._distance}|"
                f"{idx_pd - self._distance}|"
                f"{idx_nd - self._distance}",
            )

        return {
            attr.name: attr.aggregator.aggregate(results[attr.name])
            for attr in self._attribute_defs
        }

    def _predict(
            self, xref: str, xalt: str, strand: str,
            annotatable: Annotatable,
    ) -> np.ndarray:
        xref_one_hot = one_hot_encode(xref)[None, :]
        xalt_one_hot = one_hot_encode(xalt)[None, :]

        if strand == "-":
            xref_one_hot = xref_one_hot[:, ::-1, ::-1]
            xalt_one_hot = xalt_one_hot[:, ::-1, ::-1]

        y_ref = np.mean([
            self._models[m].predict(xref_one_hot, verbose=0)
            for m in range(5)
        ], axis=0)
        y_alt = np.mean([
            self._models[m].predict(xalt_one_hot, verbose=0)
            for m in range(5)
        ], axis=0)
        if strand == "-":
            y_ref = y_ref[:, ::-1]
            y_alt = y_alt[:, ::-1]

        ref_len = len(annotatable.ref)
        alt_len = len(annotatable.alt)

        if ref_len > 1 and alt_len == 1:
            y_alt = np.concatenate([
                y_alt[:, :self._distance + alt_len],
                np.zeros((1, ref_len - alt_len, 3)),
                y_alt[:, self._distance + alt_len:]],
                axis=1)
        elif ref_len == 1 and alt_len > 1:
            y_alt = np.concatenate([
                y_alt[:, :self._distance],
                np.max(
                    y_alt[:, self._distance : self._distance + alt_len],
                    axis=1)[:, None, :],
                y_alt[:, self._distance + alt_len:]],
                axis=1)

        return np.concatenate([y_ref, y_alt])

    def _seq_padding(
            self, seq: str,
            tx_region: tuple[int, int],
            annotatable: Annotatable,
    ) -> tuple[str, str]:
        padding = (
            max(self._width() // 2 + tx_region[0] - annotatable.pos, 0),
            max(self._width() // 2 - tx_region[1] + annotatable.pos, 0))
        xref = "N" * padding[0] + \
            seq[padding[0]:self._width() - padding[1]] + \
            "N" * padding[1]
        xalt = xref[:self._width() // 2] + \
            annotatable.alt + xref[self._width() // 2 + len(annotatable.ref):]
        return xref, xalt
