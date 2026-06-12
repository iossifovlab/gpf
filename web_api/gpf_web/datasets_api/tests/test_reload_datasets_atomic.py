# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0415
"""Tests for atomic, non-destructive hierarchy rebuild (iossifovlab/gpf#922).

``reload_datasets`` rebuilds the dataset-permission hierarchy by clearing
``DatasetHierarchy`` and re-inserting every relation.  Historically this ran
without an enclosing transaction, so a failure partway through the rebuild
left the hierarchy empty/partial -- and a concurrent permission check could
observe that empty state and compute an empty permitted-datasets set
("spurious 0 variants").

These tests pin the rebuild to be atomic: a failure mid-rebuild must roll
back to the previously-loaded hierarchy instead of destroying it.
"""
import pytest
from gpf_instance.gpf_instance import WGPFInstance, reload_datasets

from datasets_api.models import DatasetHierarchy


def _hierarchy_rows(instance_id: str) -> set[tuple[str, str, bool]]:
    return {
        (rel.ancestor.dataset_id, rel.descendant.dataset_id, rel.direct)
        for rel in DatasetHierarchy.objects.filter(
            instance_id=instance_id,
        ).select_related("ancestor", "descendant")
    }


def test_reload_datasets_failure_preserves_prior_hierarchy(
    custom_wgpf: WGPFInstance,
    mocker: "pytest.MockFixture",  # type: ignore[name-defined]
) -> None:
    """A failure mid-rebuild rolls back to the prior hierarchy.

    ``custom_wgpf`` has already populated the hierarchy once.  We then run
    ``reload_datasets`` again, but make ``add_relation`` raise partway through
    the re-insert loop.  With an atomic rebuild the prior hierarchy must be
    fully intact afterwards -- never observed empty or partial.
    """
    instance_id = custom_wgpf.instance_id

    before = _hierarchy_rows(instance_id)
    assert before, "precondition: hierarchy populated by custom_wgpf"

    call_count = {"n": 0}
    real_add_relation = DatasetHierarchy.add_relation.__func__  # type: ignore[attr-defined]

    # ``add_relation`` is only ever called inside the atomic swap, i.e. after
    # ``clear()`` has already deleted the prior hierarchy.  Raising on the
    # Nth call therefore lands mid re-insert -- exactly the window where a
    # non-atomic rebuild would leave the hierarchy empty/partial.  (Keep this
    # invariant in mind if the fixture's relation count ever changes: N must
    # stay > 1 and < total relations to exercise the partial-insert state.)
    def flaky_add_relation(*args: object, **kwargs: object) -> None:
        call_count["n"] += 1
        if call_count["n"] == 3:
            raise RuntimeError("induced failure mid-rebuild")
        real_add_relation(DatasetHierarchy, *args, **kwargs)

    mocker.patch.object(
        DatasetHierarchy, "add_relation",
        side_effect=flaky_add_relation,
    )

    with pytest.raises(RuntimeError, match="induced failure mid-rebuild"):
        reload_datasets(custom_wgpf)

    after = _hierarchy_rows(instance_id)
    assert after == before, (
        "hierarchy must be rolled back to its prior state after a failed "
        "rebuild; got a partial/empty hierarchy instead"
    )


def test_reload_datasets_clean_rebuild_is_idempotent(
    custom_wgpf: WGPFInstance,
) -> None:
    """A clean rebuild reproduces the exact same relation set.

    ``custom_wgpf`` has already built the hierarchy once.  Running
    ``reload_datasets`` again with no induced failure must produce an
    identical relation set -- this guards the tightened-transaction-scope
    refactor (precompute relations outside the atomic block) against
    silently changing the produced hierarchy.
    """
    instance_id = custom_wgpf.instance_id

    before = _hierarchy_rows(instance_id)
    assert before, "precondition: hierarchy populated by custom_wgpf"

    reload_datasets(custom_wgpf)

    after = _hierarchy_rows(instance_id)
    assert after == before, (
        "a clean rebuild must reproduce the exact same relation set"
    )
