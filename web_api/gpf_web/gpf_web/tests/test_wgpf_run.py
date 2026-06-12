# pylint: disable=W0212,C0116
"""Regression guard for the ``wgpf run`` dataset-hierarchy build (gpf#925).

``wgpf run`` keeps ``sys.argv == ["wgpf", "run", ...]`` and invokes
``runserver`` only as a Django sub-command argv, so the ``WDAEConfig.ready``
boot rebuild (gated on "runserver"/"gunicorn" in ``sys.argv``) never fires on
this path. ``_run_run_command`` must therefore build the hierarchy itself,
*before* it launches the server -- otherwise the dev/docs-e2e server serves
against an empty hierarchy and denies every user.
"""
import pathlib
from typing import Any
from unittest.mock import MagicMock, patch

from gpf_web import wgpf


def test_run_run_command_builds_hierarchy_before_serving(
    tmp_path: pathlib.Path,
) -> None:
    instance = MagicMock(dae_dir=str(tmp_path))

    with patch.object(wgpf, "_check_is_initialized", return_value=True), \
            patch.object(wgpf, "ReannotateInstanceTool"), \
            patch.object(wgpf, "generate_denovo_gene_sets"), \
            patch.object(wgpf, "generate_common_report"), \
            patch.object(wgpf, "ensure_dataset_hierarchy") as ensure_mock, \
            patch.object(wgpf, "execute_from_command_line") as runserver_mock:

        # The server launch must not run until the hierarchy is built.
        def _assert_hierarchy_built_first(*_args: Any, **_kwargs: Any) -> None:
            ensure_mock.assert_called_once_with(instance)

        runserver_mock.side_effect = _assert_hierarchy_built_first

        wgpf._run_run_command(instance, host="127.0.0.1", port="0")

    ensure_mock.assert_called_once_with(instance)
    runserver_mock.assert_called_once()
