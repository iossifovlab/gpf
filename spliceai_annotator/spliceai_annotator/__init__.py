from dae.annotation.annotation_config import (
    AnnotatorInfo,
)
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    Annotator,
)


def build_spliceai_annotator(
    pipeline: AnnotationPipeline,
    info: AnnotatorInfo,
) -> Annotator:
    # pylint: disable=import-outside-toplevel
    from .spliceai_annotator import SpliceAIAnnotator
    return SpliceAIAnnotator(pipeline, info)
