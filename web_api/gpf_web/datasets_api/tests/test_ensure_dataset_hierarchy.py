# pylint: disable=W0621,C0114,C0116,W0212,W0613
"""Tests for the boot-time hierarchy safety net (iossifovlab/gpf#925).

``ensure_dataset_hierarchy`` is called from ``WDAEConfig.ready`` on the
serving path so a worker never serves against an empty ``DatasetHierarchy``
(which would deny every user).  It must build the hierarchy when it is
missing, and skip the rebuild (cheaply) when it is already present.
"""
import pytest_mock
from gpf_instance.gpf_instance import (
    WGPFInstance,
    ensure_dataset_hierarchy,
)

from datasets_api.models import DatasetHierarchy


def test_ensure_builds_hierarchy_when_empty(
    custom_wgpf_module: WGPFInstance,
    db: None,  # noqa: ARG001
) -> None:
    """Against an empty hierarchy it builds and returns True."""
    instance_id = custom_wgpf_module.instance_id
    assert not DatasetHierarchy.objects.filter(
        instance_id=instance_id,
    ).exists(), "precondition: hierarchy is empty"

    built = ensure_dataset_hierarchy(custom_wgpf_module)

    assert built is True
    assert DatasetHierarchy.objects.filter(
        instance_id=instance_id,
    ).exists(), "hierarchy must be populated after the safety net runs"


def test_ensure_skips_when_already_populated(
    custom_wgpf_module: WGPFInstance,
    db: None,  # noqa: ARG001
    mocker: pytest_mock.MockFixture,
) -> None:
    """Against a populated hierarchy it does NOT rebuild and returns False."""
    # Populate the hierarchy first.
    assert ensure_dataset_hierarchy(custom_wgpf_module) is True

    # Now spy: a second call must observe the existing rows and skip.
    spy = mocker.patch("gpf_instance.gpf_instance.reload_datasets")

    built = ensure_dataset_hierarchy(custom_wgpf_module)

    assert built is False
    spy.assert_not_called()
