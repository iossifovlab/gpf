# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613

from collections.abc import Iterable, Sequence

import pytest
from dae.annotation.annotatable import (
    Annotatable,
    Position,
    Region,
)
from dae.parquet.schema2.processing_pipeline import (
    AnnotatablesBatchFilter,
    AnnotatablesWithContext,
    Annotation,
)


class DummyAnnotatablesBatchFilter(AnnotatablesBatchFilter):

    def filter_batch(
        self, batch: Iterable[Annotatable],
    ) -> Sequence[Annotation]:

        """Mock filter that returns all annotatables as annotations."""
        return [
            Annotation(
                annotatable,
                {"index": index},
            )
            for index, annotatable in enumerate(batch)
        ]


@pytest.mark.parametrize(
    "awcs",
    [
        [
            AnnotatablesWithContext(
                [
                    Position("chr1", 100),
                    Region("chr1", 200, 201),
                ],
                {"source": "1"},
            ),
        ],
        [
            AnnotatablesWithContext(
                [
                    Position("chr1", 100),
                    Region("chr1", 200, 201),
                ],
                {"source": "1"},
            ),
            AnnotatablesWithContext(
                [
                    Position("chr1", 100),
                    Region("chr1", 200, 201),
                ],
                {"source": "2"},
            ),
        ],
    ],
)
def test_filter_batches_with_context(
    awcs: Sequence[AnnotatablesWithContext],
) -> None:
    """Test filtering batches with context."""

    dummy = DummyAnnotatablesBatchFilter()
    batch_result = next(iter(dummy.filter_batches_with_context([awcs])))
    assert len(batch_result) == len(awcs)
    test_index = 0
    for annotations, annotatables in zip(
                batch_result, awcs, strict=True,
            ):

        assert len(annotations.annotations) == len(annotatables.annotatables)
        assert annotations.context == annotatables.context
        for annotation, annotatable in zip(
                    annotations.annotations, annotatables.annotatables,
                    strict=True,
                ):
            assert annotation.annotatable == annotatable
            assert annotation.annotations["index"] == test_index
            test_index += 1
