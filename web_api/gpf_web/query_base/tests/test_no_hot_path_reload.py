# pylint: disable=W0621,C0114,C0116,W0212,W0613
"""Regression guard for iossifovlab/gpf#925.

The dataset-permission hierarchy rebuild (``reload_datasets`` /
``recreated_dataset_perm``) used to run lazily on the first request a worker
served, via ``QueryBaseView.__init__``.  That put the full rebuild cost on
the request hot path and could exceed the Apache proxy timeout (502).

Constructing a ``QueryBaseView`` must no longer trigger the rebuild -- the
view treats the hierarchy as read-only.  The rebuild is moved out-of-band to
a management command (run as a deploy pre-start step).
"""
import pytest_mock
from gpf_instance.gpf_instance import WGPFInstance

from query_base.query_base import QueryBaseView


def test_constructing_query_base_view_does_not_reload_datasets(
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001
    mocker: pytest_mock.MockFixture,
) -> None:
    """Building the view must not rebuild the dataset hierarchy."""
    # Spy *after* the fixture has already built the hierarchy once, so any
    # call we observe comes from constructing the view -- the hot path.
    spy = mocker.patch("gpf_instance.gpf_instance.reload_datasets")

    QueryBaseView()

    spy.assert_not_called()
