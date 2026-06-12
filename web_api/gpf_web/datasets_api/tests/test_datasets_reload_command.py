# pylint: disable=W0621,C0114,C0116,W0212,W0613
"""Tests for the out-of-band hierarchy rebuild command (iossifovlab/gpf#925).

With the request-path trigger removed from ``QueryBaseView``, the
dataset-permission hierarchy is rebuilt out-of-band by a management command
that the deploy runs as a pre-start step (alongside DB migrations).
"""
import pytest_mock
from django.core.management import call_command
from gpf_instance.gpf_instance import WGPFInstance
from users_api.management.commands.datasets_reload import Command

from datasets_api.models import DatasetHierarchy


def _hierarchy_rows(instance_id: str) -> set[tuple[str, str, bool]]:
    return {
        (rel.ancestor.dataset_id, rel.descendant.dataset_id, rel.direct)
        for rel in DatasetHierarchy.objects.filter(
            instance_id=instance_id,
        ).select_related("ancestor", "descendant")
    }


def test_datasets_reload_command_calls_reload_datasets(
    custom_wgpf_module: WGPFInstance,
    db: None,  # noqa: ARG001
    mocker: pytest_mock.MockFixture,
) -> None:
    """Running the command rebuilds the hierarchy via ``reload_datasets``."""
    spy = mocker.patch(
        "users_api.management.commands.datasets_reload.reload_datasets",
    )

    command = Command(gpf_instance=custom_wgpf_module)
    call_command(command)

    spy.assert_called_once_with(custom_wgpf_module)


def test_datasets_reload_command_builds_hierarchy(
    custom_wgpf_module: WGPFInstance,
    db: None,  # noqa: ARG001
) -> None:
    """Running the command populates ``DatasetHierarchy`` relations."""
    instance_id = custom_wgpf_module.instance_id
    assert not _hierarchy_rows(instance_id), (
        "precondition: hierarchy is empty before the command runs"
    )

    command = Command(gpf_instance=custom_wgpf_module)
    call_command(command)

    rows = _hierarchy_rows(instance_id)
    assert rows, "command must populate the dataset hierarchy"
    # omni_dataset directly contains dataset_1 and dataset_2.
    assert (
        "omni_dataset", "dataset_1", True,
    ) in rows
    assert (
        "omni_dataset", "dataset_2", True,
    ) in rows


def test_datasets_reload_command_is_idempotent(
    custom_wgpf_module: WGPFInstance,
    db: None,  # noqa: ARG001
) -> None:
    """Running the command twice yields the same hierarchy (safe to repeat)."""
    instance_id = custom_wgpf_module.instance_id

    call_command(Command(gpf_instance=custom_wgpf_module))
    rows_after_first = _hierarchy_rows(instance_id)
    assert rows_after_first, "first run must populate the dataset hierarchy"

    call_command(Command(gpf_instance=custom_wgpf_module))
    rows_after_second = _hierarchy_rows(instance_id)

    assert rows_after_second == rows_after_first, (
        "the hierarchy relation set must be identical after a second run"
    )
