from copy import deepcopy
from typing import Any

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotation_config import AnnotatorInfo, AttributeInfo
from dae.annotation.annotation_pipeline import AnnotationPipeline, Annotator
from dae.annotation.annotator_base import AnnotatorBase


class ChromosomeAnnotator(AnnotatorBase):
    """Annotator for adjusting chromosome values."""

    def __init__(self, pipeline: AnnotationPipeline, info: AnnotatorInfo):
        assert "chrom_mapping" in info.parameters
        mapping = info.parameters["chrom_mapping"]
        assert any(
            option in mapping for option in [
                "add_prefix",
                "del_prefix",
            ]
        )

        self.add_prefix = mapping.get("add_prefix", None)
        self.del_prefix = mapping.get("del_prefix", None)

        if not info.attributes:
            info.attributes = [
                AttributeInfo(
                    "renamed_chromosome",
                    "renamed_chromosome",
                    internal=True,
                    parameters={})]
        super().__init__(pipeline, info, {
            "renamed_chromosome": (
                "annotatable", "Allele with renamed chromosome.",
            ),
        })

    def _do_annotate(
        self,
        annotatable: Annotatable,
        _context: dict[str, Any],
    ) -> dict[str, Any]:
        new_annotatable = deepcopy(annotatable)
        if self.add_prefix:
            new_chrom = f"{self.add_prefix}{new_annotatable.chrom}"
            new_annotatable._chrom = new_chrom  # noqa: SLF001
        if self.del_prefix:
            new_chrom = new_annotatable.chrom.removeprefix(self.del_prefix)
            new_annotatable._chrom = new_chrom  # noqa: SLF001
        return {"renamed_chromosome": new_annotatable}


def build_chromosome_annotator(
    pipeline: AnnotationPipeline, info: AnnotatorInfo,
) -> Annotator:
    return ChromosomeAnnotator(pipeline, info)
