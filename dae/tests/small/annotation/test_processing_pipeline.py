# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613

from collections.abc import Iterable, Sequence
from types import TracebackType
from unittest.mock import MagicMock

import pytest
from dae.annotation.annotatable import (
    Annotatable,
    Position,
    Region,
)
from dae.annotation.processing_pipeline import (
    AnnotatablesBatchFilter,
    AnnotatablesWithVariant,
    AnnotatableWithContext,
)


class DummyAnnotatablesBatchFilter(AnnotatablesBatchFilter):

    def filter_batch(
        self, batch: Iterable[Annotatable | None],
    ) -> Sequence[AnnotatableWithContext]:

        """Mock filter that returns all annotatables as annotations."""
        return [
            AnnotatableWithContext(
                annotatable,
                {"index": index},
            )
            for index, annotatable in enumerate(batch)
        ]

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            exc_tb: TracebackType | None) -> bool:
        return exc_type is not None


@pytest.mark.parametrize(
    "awcs",
    [
        [
            AnnotatablesWithVariant(
                MagicMock(),
                [
                    Position("chr1", 100),
                    Region("chr1", 200, 201),
                ],
            ),
        ],
        [
            AnnotatablesWithVariant(
                MagicMock(),
                [
                    Position("chr1", 100),
                    Region("chr1", 200, 201),
                ],
            ),
            AnnotatablesWithVariant(
                MagicMock(),
                [
                    Position("chr1", 100),
                    Region("chr1", 200, 201),
                ],
            ),
        ],
    ],
)
def test_filter_batches_with_context(
    awcs: Sequence[AnnotatablesWithVariant],
) -> None:
    """Test filtering batches with context."""

    dummy = DummyAnnotatablesBatchFilter()
    batch_result = next(iter(dummy.filter_batches_with_context([awcs])))
    assert len(batch_result) == len(awcs)
    test_index = 0
    for annotated_variant, annotatables_with_variant in zip(
        batch_result, awcs, strict=True,
    ):
        assert len(annotated_variant.awcs) == \
               len(annotatables_with_variant.annotatables)
        assert annotated_variant.variant == annotatables_with_variant.variant
        for annotation, annotatable in zip(
            annotated_variant.awcs, annotatables_with_variant.annotatables,
            strict=True,
        ):
            assert annotation.annotatable == annotatable
            assert annotation.annotation["index"] == test_index
            test_index += 1
