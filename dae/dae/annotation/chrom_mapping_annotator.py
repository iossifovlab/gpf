import textwrap
from copy import deepcopy
from typing import Any

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotation_config import AnnotatorInfo, AttributeInfo
from dae.annotation.annotation_pipeline import AnnotationPipeline, Annotator
from dae.annotation.annotator_base import AnnotatorBase
from dae.genomic_resources.utils import build_chrom_mapping


class ChromMappingAnnotator(AnnotatorBase):
    """Annotator for adjusting chromosome values."""

    def __init__(self, pipeline: AnnotationPipeline, info: AnnotatorInfo):

        mapping = info.parameters.get("mapping")
        add_prefix = info.parameters.get("add_prefix")
        del_prefix = info.parameters.get("del_prefix")
        filename = info.parameters.get("filename")

        assert filename is None

        mapping_config = {
            "chrom_mapping": {
                "mapping": mapping,
                "add_prefix": add_prefix,
                "del_prefix": del_prefix,
            },
        }
        self.chrom_mapping = build_chrom_mapping(None, mapping_config)
        if self.chrom_mapping is None:
            raise ValueError(
                "ChromosomeAnnotator requires a valid chrom_mapping config")

        if not info.attributes:
            info.attributes = [
                AttributeInfo(
                    "renamed_chromosome",
                    "renamed_chromosome",
                    internal=True,
                    parameters={})]

        info.documentation += textwrap.dedent(f"""

Annotator that maps chromsomes from one naming convention to another.

<a href="{self.BASE_DOC_URL}#chromosome-mapping-annotator" target="_blank">More info</a>

""")  # noqa

        super().__init__(pipeline, info, {
            "renamed_chromosome": (
                "annotatable", "Allele with renamed chromosome.",
            ),
        })

    def _do_annotate(
        self,
        annotatable: Annotatable,
        context: dict[str, Any],  # noqa: ARG002
    ) -> dict[str, Any]:
        new_annotatable = deepcopy(annotatable)
        assert self.chrom_mapping is not None

        new_chrom = self.chrom_mapping(new_annotatable.chrom)
        if new_chrom is None:
            return {}
        new_annotatable._chrom = new_chrom  # noqa: SLF001
        return {"renamed_chromosome": new_annotatable}


def build_chrom_mapping_annotator(
    pipeline: AnnotationPipeline, info: AnnotatorInfo,
) -> Annotator:
    return ChromMappingAnnotator(pipeline, info)
