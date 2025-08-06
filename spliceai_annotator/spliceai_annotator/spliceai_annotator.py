from __future__ import annotations

import logging
import textwrap
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import tensorflow as tf
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
from pkg_resources import resource_filename

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

    source: str
    documentation: str
    aggregator: Aggregator


@dataclass
class _AnnotationRequest:
    vcf_allele: VCFAllele
    x_ref: np.ndarray
    x_alt: np.ndarray
    strand: str
    gene: str
    transcripts: list[str]
    context: Any
    batch_index: int = -1


@dataclass
class _AnnotationResult:
    request: _AnnotationRequest
    y: np.ndarray


class SpliceAIAnnotator(AnnotatorBase):
    """SpliceAI annotator class."""
    DEFAULT_DISTANCE = 50

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
                raise ValueError(
                    f"The {info} has no reference genome"
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
        self._distance = int(info.parameters.get(
            "distance", self.DEFAULT_DISTANCE))
        if self._distance < 0 or self._distance > 5000:
            logger.warning(
                "distance %s is out of range. "
                "Setting it to 50.", self._distance,
            )
            self._distance = self.DEFAULT_DISTANCE
        logger.info(
            "SpliceAI annotator distance set to %d", self._distance,
        )
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
            if attr.source not in self._attributes_definition():
                logger.error(
                    "Attribute %s is not supported by SpliceAI annotator",
                    attr.source,
                )
                continue

            attr_config = self._attributes_definition()[attr.source]
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
                attr.source,
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
        self._models = [  # type: ignore
            tf.keras.models.load_model(
                resource_filename(__name__, path))
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

    def _annotation_requests(
        self, annotatable: Annotatable,
        context: dict[str, Any],
        batch_index: int = -1,
    ) -> list[_AnnotationRequest] | None:
        logger.debug(
            "creating annotation request for %s", annotatable)
        assert isinstance(annotatable, VCFAllele)

        if not self._is_valid_annotatable(annotatable):
            return None

        assert not (len(annotatable.ref) > 1 and len(annotatable.alt) > 1)

        transcripts = self.gene_models.gene_models_by_location(
            annotatable.chromosome,
            annotatable.pos,
        )
        if not transcripts:
            return None

        width = self._width()
        seq = self._ref_sequence(annotatable)
        if len(seq) != width:
            logger.warning(
                "Skipping record (near chromosome end): %s", annotatable,
            )
            return None
        ref_len = len(annotatable.ref)
        if seq[width // 2: width // 2 + ref_len] != annotatable.ref:
            logger.warning(
                "Skipping record (wrong reference): %s", annotatable,
            )
            return None

        genes = defaultdict(list)
        for transcript in transcripts:
            genes[transcript.gene].append(transcript)

        requests: list[_AnnotationRequest] = []
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
                return None
            strand = strands[0]

            xref, xalt = self._seq_padding(
                seq, tx, annotatable,
                batch_mode=(batch_index >= 0),
            )
            xref_one_hot = one_hot_encode(xref)[None, :]
            xalt_one_hot = one_hot_encode(xalt)[None, :]

            if strand == "-":
                xref_one_hot = xref_one_hot[:, ::-1, ::-1]
                xalt_one_hot = xalt_one_hot[:, ::-1, ::-1]

            requests.append(
                _AnnotationRequest(
                    vcf_allele=annotatable,
                    x_ref=xref_one_hot,
                    x_alt=xalt_one_hot,
                    strand=strand,
                    gene=gene,
                    transcripts=[t.tr_id for t in transcripts],
                    context=context,
                    batch_index=batch_index,
                ))
        return requests

    def _do_annotate(
        self, annotatable: Annotatable,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        assert isinstance(annotatable, VCFAllele)
        requests = self._annotation_requests(
            annotatable, context, batch_index=-1,
        )
        if requests is None:
            return self._not_found()
        assert requests is not None

        annotation_results = [
            self._predict_sequential(request)
            for request in requests
        ]
        return self._format_results(annotation_results)

    def _format_results(
        self,
        annotation_results: list[_AnnotationResult],
    ) -> dict[str, Any]:
        results: dict[str, list[Any]] = defaultdict(list)
        for res in annotation_results:
            y = res.y
            request = res.request
            idx_pa = (y[1, :, 1] - y[0, :, 1]).argmax()
            idx_na = (y[0, :, 1] - y[1, :, 1]).argmax()
            idx_pd = (y[1, :, 2] - y[0, :, 2]).argmax()
            idx_nd = (y[0, :, 2] - y[1, :, 2]).argmax()

            pa = (y[1, idx_pa, 1] - y[0, idx_pa, 1])
            na = (y[0, idx_na, 1] - y[1, idx_na, 1])
            pd = (y[1, idx_pd, 2] - y[0, idx_pd, 2])
            nd = (y[0, idx_nd, 2] - y[1, idx_nd, 2])

            results["gene"].append(request.gene)
            results["transcript_ids"].append(
                    ",".join(request.transcripts),
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
                    f"{request.vcf_allele.alt}|{request.gene}|"
                    f"{pa:.2f}|{na:.2f}|"
                    f"{pd:.2f}|{nd:.2f}|"
                    f"{idx_pa - self._distance}|"
                    f"{idx_na - self._distance}|"
                    f"{idx_pd - self._distance}|"
                    f"{idx_nd - self._distance}",
                )
        if not results:
            return self._not_found()
        return {
            attr.source: attr.aggregator.aggregate(results[attr.source])
            for attr in self._attribute_defs
        }

    def _ref_sequence(self, annotatable: VCFAllele) -> str:
        width = self._width()
        return self.genome.get_sequence(
            annotatable.chromosome,
            annotatable.pos - width // 2,
            annotatable.pos + width // 2,
        )

    def _predict_sequential(
            self, req: _AnnotationRequest,
    ) -> _AnnotationResult:

        assert self._models is not None
        y_ref = np.mean([
            self._models[m].predict(req.x_ref, verbose=0)
            for m in range(5)
        ], axis=0)
        y_alt = np.mean([
            self._models[m].predict(req.x_alt, verbose=0)
            for m in range(5)
        ], axis=0)
        y = self._prediction_padding_sequential(req, y_ref, y_alt)

        return _AnnotationResult(req, y)

    def _prediction_padding_sequential(
        self, req: _AnnotationRequest,
        y_ref: np.ndarray, y_alt: np.ndarray,
    ) -> np.ndarray:
        logger.debug("processing prediction for %s", req.vcf_allele)
        if req.strand == "-":
            y_ref = y_ref[:, ::-1]
            y_alt = y_alt[:, ::-1]
        ref_len = len(req.vcf_allele.ref)
        alt_len = len(req.vcf_allele.alt)

        if ref_len > 1 and alt_len == 1:
            # deletion
            y_alt = np.concatenate([
                y_alt[:, :self._distance + alt_len],
                np.zeros((1, ref_len - alt_len, 3)),
                y_alt[:, self._distance + alt_len:]],
                axis=1)
        elif ref_len == 1 and alt_len > 1:
            # insertion
            y_alt = np.concatenate([
                y_alt[:, :self._distance],
                np.max(
                    y_alt[:, self._distance: self._distance + alt_len],
                    axis=1)[:, None, :],
                y_alt[:, self._distance + alt_len:]],
                axis=1)

        return np.concatenate([y_ref, y_alt])

    def _prediction_padding_batch(
        self, req: _AnnotationRequest,
        y_ref: np.ndarray, y_alt: np.ndarray,
    ) -> np.ndarray:
        logger.debug("processing prediction for %s", req.vcf_allele)
        if req.strand == "-":
            y_ref = y_ref[:, ::-1]
            y_alt = y_alt[:, ::-1]
        ref_len = len(req.vcf_allele.ref)
        alt_len = len(req.vcf_allele.alt)
        if ref_len > 1 and alt_len == 1:
            y_alt = np.concatenate([
                y_alt[:, :self._distance + alt_len],
                np.zeros((1, min(self._distance, ref_len - 1), 3)),
                y_alt[:, self._distance + 1:-(ref_len - 1)]],
                axis=1)
        elif ref_len == 1 and alt_len > 1:
            # insertion
            y_alt = np.concatenate([
                y_alt[:, :self._distance],
                np.max(
                    y_alt[:, self._distance: self._distance + alt_len],
                    axis=1)[:, None, :],
                y_alt[:, self._distance + alt_len:]],
                axis=1)

        assert y_ref.shape == y_alt.shape, (
            f"y_ref shape {y_ref.shape} != y_alt shape {y_alt.shape}; "
            f"allele: {req.vcf_allele}")

        return np.concatenate([y_ref, y_alt])

    def _predict_batch(
        self, reqs: Sequence[_AnnotationRequest],
    ) -> list[_AnnotationResult]:
        assert self._models is not None
        assert len(reqs) > 0
        assert all(reqs[0].x_alt.shape == req.x_alt.shape
                   for req in reqs)

        x_ref_batch = np.concatenate(
            [req.x_ref for req in reqs], axis=0)
        x_alt_batch = np.concatenate(
            [req.x_alt for req in reqs], axis=0)
        logger.debug(
            "predicting a batch of request: %s; %s", len(reqs),
            x_alt_batch.shape,
        )
        y_ref_batch = np.mean([
            self._models[m].predict(x_ref_batch, verbose=0)
            for m in range(5)
        ], axis=0)
        y_alt_batch = np.mean([
            self._models[m].predict(x_alt_batch, verbose=0)
            for m in range(5)
        ], axis=0)

        logger.debug(
            "transforming results",
        )
        results = []
        for i, req in enumerate(reqs):
            x_ref = y_ref_batch[i:i + 1, :, :]
            x_alt = y_alt_batch[i:i + 1, :, :]
            y = self._prediction_padding_batch(req, x_ref, x_alt)
            results.append(_AnnotationResult(req, y))
        logger.debug(
            "returning results: %d", len(results),
        )
        return results

    def _seq_padding(
            self, seq: str,
            tx_region: tuple[int, int],
            annotatable: Annotatable, *,
            batch_mode: bool = False,
    ) -> tuple[str, str]:
        assert isinstance(annotatable, VCFAllele)
        padding = (
            max(self._width() // 2 + tx_region[0] - annotatable.pos, 0),
            max(self._width() // 2 - tx_region[1] + annotatable.pos, 0))
        xref = "N" * padding[0] + \
            seq[padding[0]:self._width() - padding[1]] + \
            "N" * padding[1]
        xalt = xref[:self._width() // 2] + \
            annotatable.alt + xref[self._width() // 2 + len(annotatable.ref):]

        if batch_mode and len(xref) > len(xalt):
            # deletions
            xalt = xalt.ljust(len(xref), "N")
            assert len(xref) == len(xalt)

        return xref, xalt

    def _do_batch_annotate(
        self,
        annotatables: Sequence[Annotatable | None],
        contexts: list[dict[str, Any]],
        batch_work_dir: str | None = None,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        annotations: dict[int, list[_AnnotationResult]] = defaultdict(list)

        batches = defaultdict(list)
        for batch_index, (annotatable, context) in enumerate(zip(
                annotatables, contexts, strict=True)):
            if not isinstance(annotatable, VCFAllele):
                annotations[batch_index] = []
                continue
            requests = self._annotation_requests(
                annotatable, context, batch_index,
            )
            if requests is None:
                annotations[batch_index] = []
                continue
            for request in requests:
                batches[request.x_alt.shape[1]].append(request)
        logger.debug(
            "batching requests: %s", {k: len(v) for k, v in batches.items()},
        )
        for batch_index, batch_requests in enumerate(batches.values()):
            logger.debug(
                "processing batch %d/%d with %d requests",
                batch_index + 1, len(batches), len(batch_requests),
            )
            if len(batch_requests) == 0:
                continue
            for bresult in self._predict_batch(batch_requests):
                batch_index = bresult.request.batch_index
                annotations[batch_index].append(bresult)

        results = []
        for _batch_index, res in sorted(annotations.items()):
            if len(res) == 0:
                results.append(self._not_found())
                continue

            results.append(self._format_results(res))

        return results
