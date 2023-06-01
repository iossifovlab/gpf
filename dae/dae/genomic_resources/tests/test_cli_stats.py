# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import textwrap
from typing import List

import pytest

from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.histogram import NumberHistogram
from dae.genomic_resources.testing import \
    setup_directories, build_filesystem_test_repository, \
    setup_tabix
from dae.genomic_resources.resource_implementation import \
    GenomicResourceImplementation, ResourceStatistics

from dae.genomic_resources.cli import cli_manage
from dae.genomic_resources import register_implementation
from dae.genomic_resources.genomic_scores import MinMaxValue

from dae.task_graph.graph import Task


class SomeTestImplementation(GenomicResourceImplementation):
    """Simple implementation used for testing."""

    STATISTICS_FOLDER = "statistics"

    def calc_statistics_hash(self) -> bytes:
        """
        Compute the statistics hash.

        This hash is used to decide whether the resource statistics should be
        recomputed.
        """
        return b"somehash"

    def add_statistics_build_tasks(self, task_graph, **kwargs) -> List[Task]:
        """Add tasks for calculating resource statistics to a task graph."""
        task = task_graph.create_task(
            "test_resource_sample_statistic",
            self._do_sample_statistic,
            [],
            []
        )
        return [task]

    def _do_sample_statistic(self):
        proto = self.resource.proto
        with proto.open_raw_file(
            self.resource, f"{self.STATISTICS_FOLDER}/somestat", mode="wt"
        ) as outfile:
            outfile.write("test")
        return True

    def get_statistics(self):
        return TestStatistics.build_statistics(self)

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


class TestStatistics(ResourceStatistics):
    @staticmethod
    def build_statistics(genomic_resource):
        return TestStatistics(genomic_resource.resource_id)


def build_test_implementation(resource):
    return SomeTestImplementation(resource)


@pytest.fixture(scope="module")
def register_test_implementation():
    register_implementation("test_resource", build_test_implementation)


def test_cli_stats(tmp_path, register_test_implementation):
    setup_directories(tmp_path, {
        "one": {
            GR_CONF_FILE_NAME: """
                type: test_resource
                some_random_value: test
                """,
        }
    })

    repo = build_filesystem_test_repository(tmp_path)

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


def test_stats_allele_score(tmp_path):
    setup_directories(tmp_path, {
        "one": {
            GR_CONF_FILE_NAME: """
                type: allele_score
                table:
                    filename: data.txt.gz
                    format: tabix
                scores:
                    - id: freq
                      type: float
                      desc: ""
                      name: freq
                histograms:
                    - score: freq
                      bins: 100
                      min: 0
                      max: 1
                      x_scale: linear
                      y_scale: log
                """
        }
    })
    setup_tabix(
        tmp_path / "one" / "data.txt.gz",
        """
        #chrom  pos_begin  reference  alternative  freq
        1      10         A          G            0.02
        1      10         A          C            0.03
        1      10         A          A            0.04
        1      16         CA         G            0.03
        1      16         C          T            0.04
        1      16         C          A            0.05
        2      16         CA         G            0.03
        2      16         C          T            EMPTY
        2      16         C          A            0.05
        """, seq_col=0, start_col=1, end_col=1)

    repo = build_filesystem_test_repository(tmp_path)

    assert repo is not None

    cli_manage(["repo-stats", "-R", str(tmp_path), "-j", "1"])
    minmax_statistic_path = os.path.join(
        tmp_path, "one", "statistics", "min_max_freq.yaml"
    )
    histogram_statistic_path = os.path.join(
        tmp_path, "one", "statistics", "histogram_freq.yaml"
    )
    histogram_image_path = os.path.join(
        tmp_path, "one", "statistics", "histogram_freq.yaml"
    )
    assert os.path.exists(minmax_statistic_path)
    assert os.path.exists(histogram_statistic_path)
    assert os.path.exists(histogram_image_path)

    with open(histogram_statistic_path, "r") as infile:
        freq_hist = NumberHistogram.deserialize(infile.read())

    assert len(freq_hist.bars) == 100
    assert freq_hist.bars[0] == 0
    assert freq_hist.bars[2] == 1  # region [10]
    assert freq_hist.bars[3] == 3  # region [10, 16, 16]
    assert freq_hist.bars[4] == 2  # region [10, 16]
    assert freq_hist.bars[5] == 2  # region [16, 16]
    assert freq_hist.bars.sum() == (1 + 3 + 2 + 2)


def test_stats_position_score(tmp_path):
    setup_directories(tmp_path, {
        "one": {
            GR_CONF_FILE_NAME: """
                type: position_score
                table:
                    filename: data.txt.gz
                    format: tabix
                scores:
                    - id: phastCons100way
                      type: float
                      desc: "The phastCons computed over the tree of 100 \
                              verterbarte species"
                      name: s1
                    - id: phastCons5way
                      type: int
                      position_aggregator: max
                      na_values: "-1"
                      desc: "The phastCons computed over the tree of 5 \
                              verterbarte species"
                      name: s2
                histograms:
                    - score: phastCons100way
                      bins: 100
                      min: 0
                      max: 1
                      x_scale: linear
                      y_scale: linear
                    - score: phastCons5way
                      bins: 4
                      min: 0
                      max: 4
                      x_scale: linear
                      y_scale: linear
                """
        }
    })
    setup_tabix(
        tmp_path / "one" / "data.txt.gz",
        """
        #chrom  pos_begin  pos_end  s1    s2
        1      10         15       0.02  -1
        1      17         19       0.03  0
        1      22         25       0.46  EMPTY
        2      5          80       0.01  3
        2      10         11       0.02  3
        """, seq_col=0, start_col=1, end_col=2)

    repo = build_filesystem_test_repository(tmp_path)

    assert repo is not None

    cli_manage(["repo-stats", "-R", str(tmp_path), "-j", "1"])
    minmax_100way_path = os.path.join(
        tmp_path, "one", "statistics", "min_max_phastCons100way.yaml"
    )
    histogram_100way_path = os.path.join(
        tmp_path, "one", "statistics", "histogram_phastCons100way.yaml"
    )
    histogram_image_100way_path = os.path.join(
        tmp_path, "one", "statistics", "histogram_phastCons100way.png"
    )
    minmax_5way_path = os.path.join(
        tmp_path, "one", "statistics", "min_max_phastCons5way.yaml"
    )
    histogram_5way_path = os.path.join(
        tmp_path, "one", "statistics", "histogram_phastCons5way.yaml"
    )
    histogram_image_5way_path = os.path.join(
        tmp_path, "one", "statistics", "histogram_phastCons5way.png"
    )
    assert os.path.exists(minmax_100way_path)
    assert os.path.exists(histogram_100way_path)
    assert os.path.exists(histogram_image_100way_path)
    assert os.path.exists(minmax_5way_path)
    assert os.path.exists(histogram_5way_path)
    assert os.path.exists(histogram_image_5way_path)

    with open(histogram_100way_path, "r") as infile:
        phast_cons_100way_hist = NumberHistogram.deserialize(infile.read())
    with open(histogram_5way_path, "r") as infile:
        phast_cons_5way_hist = NumberHistogram.deserialize(infile.read())

    assert len(phast_cons_100way_hist.bars) == 100
    assert phast_cons_100way_hist.bars[0] == 0
    assert phast_cons_100way_hist.bars[1] == 76  # region [5-80]
    assert phast_cons_100way_hist.bars[2] == 8  # region [10-15] and [10-11]
    assert phast_cons_100way_hist.bars[3] == 3  # region [17-19]
    assert phast_cons_100way_hist.bars[4] == 0
    assert phast_cons_100way_hist.bars[46] == 4  # region [22-24]
    assert phast_cons_100way_hist.bars.sum() == (76 + 8 + 3 + 4)

    assert len(phast_cons_5way_hist.bars) == 4
    assert phast_cons_5way_hist.bars[0] == 3  # region [17-19]
    assert phast_cons_5way_hist.bars[3] == 76 + 2  # region [5-80] and [10-11]
    assert phast_cons_5way_hist.bars.sum() == (76 + 2 + 3)


def test_stats_np_score(tmp_path):
    setup_directories(tmp_path, {
        "one": {
            GR_CONF_FILE_NAME: """
                type: np_score
                table:
                    filename: data.txt.gz
                    format: tabix
                scores:
                    - id: cadd_raw
                      type: float
                      desc: ""
                      name: s1
                    - id: cadd_test
                      type: int
                      position_aggregator: max
                      nucleotide_aggregator: mean
                      na_values: "-1"
                      desc: ""
                      name: s2
                histograms:
                    - score: cadd_raw
                      bins: 100
                      min: 0
                      max: 1
                      x_scale: linear
                      y_scale: linear
                    - score: cadd_test
                      bins: 4
                      min: 0
                      max: 4
                      x_scale: linear
                      y_scale: linear
            """
        }
    })
    setup_tabix(
        tmp_path / "one" / "data.txt.gz",
        """
        #chrom  pos_begin  pos_end  reference  alternative  s1    s2
        1      10         15       A          G            0.02  2
        1      10         15       A          C            0.03  -1
        1      10         15       A          T            0.04  4
        1      16         19       C          G            0.03  3
        1      16         19       C          T            0.04  EMPTY
        1      16         19       C          A            0.05  0
        2      16         19       C          A            0.03  3
        2      16         19       C          T            0.04  3
        2      16         19       C          G            0.05  4
        """, seq_col=0, start_col=1, end_col=2)

    repo = build_filesystem_test_repository(tmp_path)

    assert repo is not None

    cli_manage(["repo-stats", "-R", str(tmp_path), "-j", "1"])
    minmax_cadd_raw_path = os.path.join(
        tmp_path, "one", "statistics", "min_max_cadd_raw.yaml"
    )
    histogram_cadd_raw_path = os.path.join(
        tmp_path, "one", "statistics", "histogram_cadd_raw.yaml"
    )
    histogram_image_cadd_raw_path = os.path.join(
        tmp_path, "one", "statistics", "histogram_cadd_raw.png"
    )
    minmax_cadd_test_path = os.path.join(
        tmp_path, "one", "statistics", "min_max_cadd_test.yaml"
    )
    histogram_cadd_test_path = os.path.join(
        tmp_path, "one", "statistics", "histogram_cadd_test.yaml"
    )
    histogram_image_cadd_test_path = os.path.join(
        tmp_path, "one", "statistics", "histogram_cadd_test.png"
    )
    assert os.path.exists(minmax_cadd_raw_path)
    assert os.path.exists(histogram_cadd_raw_path)
    assert os.path.exists(histogram_image_cadd_raw_path)
    assert os.path.exists(minmax_cadd_test_path)
    assert os.path.exists(histogram_cadd_test_path)
    assert os.path.exists(histogram_image_cadd_test_path)

    with open(histogram_cadd_raw_path, "r") as infile:
        cadd_raw_hist = NumberHistogram.deserialize(infile.read())
    with open(histogram_cadd_test_path, "r") as infile:
        cadd_test_hist = NumberHistogram.deserialize(infile.read())

    assert len(cadd_raw_hist.bars) == 100
    assert cadd_raw_hist.bars[2] == 6  # region [10-15]
    assert cadd_raw_hist.bars[3] == 14  # region [10-15], 2x[16-19]
    assert cadd_raw_hist.bars[4] == 14  # region [10-15], 2x[16-19]
    assert cadd_raw_hist.bars[5] == 8  # region 2x[16-19]
    assert cadd_raw_hist.bars.sum() == (6 + 14 + 14 + 8)

    assert len(cadd_test_hist.bars) == 4
    assert cadd_test_hist.bars[0] == 4  # region [16-19]
    assert cadd_test_hist.bars[2] == 6  # region [10-15]
    assert cadd_test_hist.bars[3] == 22  # region [10-15]
    assert cadd_test_hist.bars.sum() == (4 + 6 + 22)


def test_minmax(tmp_path):
    setup_directories(tmp_path, {
        "one": {
            GR_CONF_FILE_NAME: """
                type: position_score
                table:
                    filename: data.txt.gz
                    format: tabix
                scores:
                    - id: phastCons100way
                      type: float
                      desc: "The phastCons computed over the tree of 100 \
                              verterbarte species"
                      name: s1
                histograms:
                    - score: phastCons100way
                      bins: 100
                      x_scale: linear
                      y_scale: linear
            """
        }
    })
    setup_tabix(
        tmp_path / "one" / "data.txt.gz",
        """
        #chrom  pos_begin  pos_end  s1
        1      10         15       0.0
        1      17         19       0.03
        1      22         25       0.46
        2      5          80       0.01
        2      10         11       1.0
        3      5          17       1.0
        3      18         20       0.01
        """, seq_col=0, start_col=1, end_col=2)

    repo = build_filesystem_test_repository(tmp_path)

    assert repo is not None

    cli_manage(["repo-stats", "-R", str(tmp_path), "-j", "1"])

    minmax_100way_path = os.path.join(
        tmp_path, "one", "statistics", "min_max_phastCons100way.yaml"
    )
    assert os.path.exists(minmax_100way_path)

    with open(minmax_100way_path, "r") as infile:
        minmax = MinMaxValue.deserialize(infile.read())

    assert minmax.min == 0
    assert minmax.max == 1


def test_reference_genome_usage(tmp_path, mocker):
    setup_directories(tmp_path, {
        "one": {
            GR_CONF_FILE_NAME: """
                type: position_score
                table:
                    filename: data.txt.gz
                    format: tabix
                scores:
                    - id: phastCons100way
                      type: float
                      desc: "The phastCons computed over the tree of 100 \
                              verterbarte species"
                      name: s1
                histograms:
                    - score: phastCons100way
                      bins: 100
                      x_scale: linear
                      y_scale: linear
                meta:
                    labels:
                        reference_genome: genome
            """
        },
        "genome": {
            GR_CONF_FILE_NAME: """
                type: genome
                filename: data.fa
            """,
            "data.fa": textwrap.dedent("""
                >1
                NACGTNACGT
                NACGTNACGT
                NACGTNACGT
                >2
                NACGTNACGT
                NACGTNACGT
                NACGTNACGT
                >3
                NACGTNACGT
                NACGTNACGT
                NACGTNACGT
            """),
            "data.fa.fai": textwrap.dedent("""\
                1	30	3	10	11
                2	30	39	10	11
                3	30	75	10	11
            """)

        }
    })
    setup_tabix(
        tmp_path / "one" / "data.txt.gz",
        """
        #chrom  pos_begin  pos_end  s1
        1      10         15       0.0
        1      17         19       0.03
        1      22         25       0.46
        2      5          8        0.01
        2      10         11       1.0
        3      5          17       1.0
        3      18         20       0.01
        """, seq_col=0, start_col=1, end_col=2)

    repo = build_filesystem_test_repository(tmp_path)

    assert repo is not None

    ref_genome_length_mock = mocker.Mock(return_value=30)
    mocker.patch(
        "dae.genomic_resources.reference_genome"
        ".ReferenceGenome.get_chrom_length",
        new=ref_genome_length_mock
    )
    assert ref_genome_length_mock.call_count == 0
    cli_manage([
        "resource-stats", "-r", "one", "-R", str(tmp_path), "-j", "1"
    ])
    assert ref_genome_length_mock.call_count == 6

    labels_mock = mocker.Mock(return_value={})
    mocker.patch(
        "dae.genomic_resources.repository."
        "GenomicResource.get_labels",
        new=labels_mock
    )

    genomic_table_length_mock = mocker.Mock(return_value=30)
    mocker.patch(
        "dae.genomic_resources.genomic_scores.get_chromosome_length_tabix",
        new=genomic_table_length_mock
    )

    os.remove(os.path.join(tmp_path, "one", "statistics", "stats_hash"))

    assert genomic_table_length_mock.call_count == 0

    cli_manage([
        "resource-stats", "-r", "one", "-R", str(tmp_path), "-j", "1"
    ])

    assert genomic_table_length_mock.call_count == 6
    assert ref_genome_length_mock.call_count == 6
