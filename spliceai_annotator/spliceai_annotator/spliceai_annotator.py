from __future__ import annotations

import logging

from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    Annotator,
    AnnotatorInfo,
)

logger = logging.getLogger(__name__)


def build_spliceai_annotator(
    pipeline: AnnotationPipeline,
    info: AnnotatorInfo,
) -> Annotator:
    raise NotImplementedError("SpliceAI annotator not implemented yet")
