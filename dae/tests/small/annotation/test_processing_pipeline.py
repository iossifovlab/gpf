# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613

from collections.abc import Iterable, Sequence
from types import TracebackType
from unittest.mock import MagicMock

import pytest
from dae.annotation.annotatable import (
    Position,
    Region,
)
from dae.annotation.processing_pipeline import (
    AnnotatablesBatchFilter,
    AnnotatableWithContext,
    VariantWithAWCs,
)


class DummyAnnotatablesBatchFilter(AnnotatablesBatchFilter):

    def filter_awc_batch(
        self, batch: Iterable[AnnotatableWithContext],
    ) -> Sequence[AnnotatableWithContext]:

        """Mock filter that returns all annotatables as annotations."""
        return [
            AnnotatableWithContext(
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
        return exc_type is not None


@pytest.mark.parametrize(
    "variants",
    [
        [
            VariantWithAWCs(
                MagicMock(),
                [
                    AnnotatableWithContext(annotatable=Position("chr1", 100)),
                    AnnotatableWithContext(annotatable=Region("chr1", 200, 201)),  # noqa: E501
                ],
            ),
        ],
        [
            VariantWithAWCs(
                MagicMock(),
                [
                    AnnotatableWithContext(annotatable=Position("chr1", 100)),
                    AnnotatableWithContext(annotatable=Region("chr1", 200, 201)),  # noqa: E501
                ],
            ),
            VariantWithAWCs(
                MagicMock(),
                [
                    AnnotatableWithContext(annotatable=Position("chr1", 100)),
                    AnnotatableWithContext(annotatable=Region("chr1", 200, 201)),  # noqa: E501
                ],
            ),
        ],
    ],
)
def test_filter_batches_with_context(
    variants: Sequence[VariantWithAWCs],
) -> None:
    """Test filtering batches with context."""

    dummy = DummyAnnotatablesBatchFilter()
    batch_result = dummy.filter_batch(variants)
    assert len(batch_result) == len(variants)
    test_index = 0
    for annotations, variant in zip(
        batch_result, variants, strict=True,
    ):
        assert len(annotations.awcs) == len(variant.awcs)
        assert annotations.variant == variant.variant
        for new_awc, old_awc in zip(
            annotations.awcs, variant.awcs, strict=True,
        ):
            assert new_awc.annotatable == old_awc.annotatable
            assert new_awc.context["index"] == test_index
            test_index += 1
