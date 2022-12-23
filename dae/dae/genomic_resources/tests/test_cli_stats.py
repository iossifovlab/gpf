# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import textwrap

import pytest

from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.testing import build_testing_repository
from dae.genomic_resources.resource_implementation import \
    GenomicResourceImplementation

from dae.genomic_resources.cli import cli_manage
from dae.genomic_resources import register_implementation


class SomeTestImplementation(GenomicResourceImplementation):
    """Simple implementation used for testing."""

    STATISTICS_FOLDER = "statistics"

    def calc_statistics_hash(self) -> str:
        """
        Compute the statistics hash.

        This hash is used to decide whether the resource statistics should be
        recomputed.
        """
        return "somehash"

    def add_statistics_build_tasks(self, task_graph) -> None:
        """Add tasks for calculating resource statistics to a task graph."""
        task_graph.create_task(
            "test_resource_sample_statistic",
            self._do_sample_statistic,
            [],
            []
        )

    def _do_sample_statistic(self):
        proto = self.resource.proto
        with proto.open_raw_file(
            self.resource, f"{self.STATISTICS_FOLDER}/somestat", mode="wt"
        ) as outfile:
            outfile.write("test")
        return True

    def calc_info_hash(self):
        """Compute and return the info hash."""
        return "infohash"

    def get_info(self) -> str:
        """Construct the contents of the implementation's HTML info page."""
        return textwrap.dedent(
            """
            <h1>Test page</h1>
            """
        )


def build_test_implementation(resource):
    return SomeTestImplementation(resource)


@pytest.fixture(scope="module")
def register_test_implementation():
    register_implementation("test_resource", build_test_implementation)


def test_cli_stats(tmp_path, register_test_implementation):
    repo = build_testing_repository(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "one": {
                GR_CONF_FILE_NAME: """
                    type: test_resource
                    some_random_value: test
                    """,
            }
        }
    )

    assert repo is not None

    cli_manage(["repo-stats", "-R", str(tmp_path), "-j", "1"])

    statistic_path = os.path.join(tmp_path, "one", "statistics", "somestat")
    assert os.path.exists(statistic_path)
    with open(statistic_path) as infile:
        assert infile.read() == "test"
    statistic_hash_path = os.path.join(
        tmp_path, "one", "statistics", "stats_hash"
    )
    assert os.path.exists(statistic_hash_path)
    with open(statistic_hash_path) as infile:
        assert infile.read() == "somehash"
