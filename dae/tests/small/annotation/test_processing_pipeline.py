# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613

from collections.abc import Iterable, Sequence
from types import TracebackType

import pytest
from dae.annotation.annotatable import (
    Position,
    Region,
)
from dae.annotation.processing_pipeline import (
    Annotation,
    AnnotationsWithSource,
    AnnotationsWithSourceBatchFilter,
)


class DummyAnnotatablesBatchFilter(AnnotationsWithSourceBatchFilter):

    def _filter_annotation_batch(
        self, batch: Iterable[Annotation],
    ) -> Sequence[Annotation]:

        """Mock filter that returns all annotatables as annotations."""
        return [
            Annotation(
                awc.annotatable,
                {"index": index},
            )
            for index, awc in enumerate(batch)
        ]

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            exc_tb: TracebackType | None) -> bool:
        return exc_type is None


@pytest.mark.parametrize(
    "aws_batch",
    [
        [
            AnnotationsWithSource(
                {"source": "1"},
                [
                    Annotation(annotatable=Position("chr1", 100)),
                    Annotation(annotatable=Region("chr1", 200, 201)),
                ],
            ),
        ],
        [
            AnnotationsWithSource(
                {"source": "1"},
                [
                    Annotation(annotatable=Position("chr1", 100)),
                    Annotation(annotatable=Region("chr1", 200, 201)),
                ],
            ),
            AnnotationsWithSource(
                {"source": "2"},
                [
                    Annotation(annotatable=Position("chr1", 100)),
                    Annotation(annotatable=Region("chr1", 200, 201)),
                ],
            ),
        ],
    ],
)
def test_filter_batches_with_source(
    aws_batch: Sequence[AnnotationsWithSource],
) -> None:
    """Test filtering batches with source."""

    dummy = DummyAnnotatablesBatchFilter()
    batch_result = dummy.filter(aws_batch)
    assert len(batch_result) == len(aws_batch)
    test_index = 0
    for result, aws in zip(
        batch_result, aws_batch, strict=True,
    ):
        assert len(result.annotations) == len(aws.annotations)
        assert result.source == aws.source
        for new_annotation, old_annotation in zip(
            result.annotations, aws.annotations, strict=True,
        ):
            assert new_annotation.annotatable == old_annotation.annotatable
            assert new_annotation.context["index"] == test_index
            test_index += 1
