# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
import pathlib
import textwrap

import pytest
from gain.gene_scores.gene_scores import ScoreDef
from gain.gene_scores.implementations.gene_scores_impl import (
    GeneScoreImplementation,
    build_gene_score_implementation_from_resource,
)
from gain.genomic_resources.histogram import (
    CategoricalHistogram,
    NullHistogramConfig,
    NumberHistogram,
)
from gain.genomic_resources.repository import (
    GR_CONF_FILE_NAME,
    GenomicResourceRepo,
)
from gain.genomic_resources.testing import (
    build_filesystem_test_repository,
    build_inmemory_test_repository,
    setup_directories,
)
from gain.task_graph.graph import TaskDesc
from jinja2 import Template

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

LINEAR_HIST_JSON = json.dumps({
    "bars": [2, 2, 2],
    "bins": [1.0, 1.665, 2.333, 3.0],
    "min_value": 1.0,
    "max_value": 3.0,
    "config": {
        "type": "number",
        "number_of_bins": 3,
        "view_range": {"min": 1.0, "max": 3.0},
        "x_log_scale": False,
        "y_log_scale": False,
    },
})

GRR_CONTENTS: dict = {
    "LinearScore": {
        GR_CONF_FILE_NAME: textwrap.dedent("""
            type: gene_score
            filename: scores.csv
            scores:
            - id: score1
              column_name: score_col
              desc: a numeric score
              small_values_desc: "low is bad"
              large_values_desc: "high is good"
              histogram:
                type: number
                number_of_bins: 3
                x_log_scale: false
                y_log_scale: false
        """),
        "scores.csv": textwrap.dedent("""
            gene,score_col
            G1,1
            G2,2
            G3,1
            G4,2
            G5,3
            G6,3
        """),
        "statistics": {
            "histogram_score1.json": LINEAR_HIST_JSON,
        },
    },
}


@pytest.fixture
def inmemory_repo() -> GenomicResourceRepo:
    return build_inmemory_test_repository(GRR_CONTENTS)


@pytest.fixture
def fs_repo(tmp_path: pathlib.Path) -> GenomicResourceRepo:
    setup_directories(tmp_path, GRR_CONTENTS)
    return build_filesystem_test_repository(tmp_path)


@pytest.fixture
def linear_impl(inmemory_repo: GenomicResourceRepo) -> GeneScoreImplementation:
    res = inmemory_repo.get_resource("LinearScore")
    return GeneScoreImplementation(res)


# ---------------------------------------------------------------------------
# build_gene_score_implementation_from_resource factory
# ---------------------------------------------------------------------------

def test_factory_creates_impl(inmemory_repo: GenomicResourceRepo) -> None:
    res = inmemory_repo.get_resource("LinearScore")
    impl = build_gene_score_implementation_from_resource(res)
    assert isinstance(impl, GeneScoreImplementation)


def test_factory_raises_on_none() -> None:
    with pytest.raises((ValueError, AttributeError)):
        build_gene_score_implementation_from_resource(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# __init__ wires up gene_score attribute
# ---------------------------------------------------------------------------

def test_init_builds_gene_score(
    inmemory_repo: GenomicResourceRepo,
) -> None:
    res = inmemory_repo.get_resource("LinearScore")
    impl = GeneScoreImplementation(res)
    assert impl.gene_score is not None
    assert impl.gene_score.get_scores() == ["score1"]


# ---------------------------------------------------------------------------
# get_template / _get_template_data
# ---------------------------------------------------------------------------

def test_get_template_returns_template(
    linear_impl: GeneScoreImplementation,
) -> None:
    tmpl = linear_impl.get_template()
    assert isinstance(tmpl, Template)


def test_get_template_data_contains_gene_score(
    linear_impl: GeneScoreImplementation,
) -> None:
    data = linear_impl._get_template_data()
    assert "gene_score" in data
    assert data["gene_score"] is linear_impl.gene_score


# ---------------------------------------------------------------------------
# get_info / get_statistics_info
# ---------------------------------------------------------------------------

def test_get_info_returns_html_with_score_id(
    linear_impl: GeneScoreImplementation,
) -> None:
    html = linear_impl.get_info()
    assert isinstance(html, str)
    assert len(html) > 0
    assert "score1" in html


def test_get_info_contains_description(
    linear_impl: GeneScoreImplementation,
) -> None:
    html = linear_impl.get_info()
    assert "a numeric score" in html


def test_get_statistics_info_returns_html(
    linear_impl: GeneScoreImplementation,
) -> None:
    html = linear_impl.get_statistics_info()
    assert isinstance(html, str)
    assert len(html) > 0


# ---------------------------------------------------------------------------
# create_statistics_build_tasks
# ---------------------------------------------------------------------------

def test_create_statistics_build_tasks_count(
    linear_impl: GeneScoreImplementation,
) -> None:
    # 1 score -> 2 tasks: calc + save
    tasks = linear_impl.create_statistics_build_tasks()
    assert len(tasks) == 1
    assert all(isinstance(t, TaskDesc) for t in tasks)


def test_create_statistics_build_tasks_ids_contain_score(
    linear_impl: GeneScoreImplementation,
) -> None:
    tasks = linear_impl.create_statistics_build_tasks()
    task_ids = [t.task.task_id for t in tasks]
    assert any("LinearScore" in tid for tid in task_ids)


def test_create_statistics_build_tasks_skips_null_histogram(
    linear_impl: GeneScoreImplementation,
) -> None:
    # NullHistogramConfig is rejected by GeneScore.__init__, so we must
    # inject it into score_definitions to exercise the skip branch.

    linear_impl.gene_score.score_definitions["null_score"] = ScoreDef(
        resource_id=linear_impl.resource.resource_id,
        score_id="null_score",
        column_name="null_score",
        description="injected null",
        value_type="float",
        hist_conf=NullHistogramConfig(reason="disabled"),
        small_values_desc=None,
        large_values_desc=None,
    )

    histograms = GeneScoreImplementation._build_histograms(
        linear_impl.resource)
    # score1 -> 2 tasks; null_score -> 0 tasks (skipped)
    assert len(histograms) == 1
    assert not any("null_score" in score_id for score_id in histograms)


def test_create_statistics_build_tasks_multiple_scores() -> None:
    repo = build_inmemory_test_repository({
        "MultiScore": {
            GR_CONF_FILE_NAME: textwrap.dedent("""
                type: gene_score
                filename: scores.csv
                scores:
                - id: alpha
                  desc: first score
                  histogram:
                    type: number
                    number_of_bins: 3
                    x_log_scale: false
                    y_log_scale: false
                - id: beta
                  desc: second score
                  histogram:
                    type: number
                    number_of_bins: 3
                    x_log_scale: false
                    y_log_scale: false
            """),
            "scores.csv": textwrap.dedent("""
                gene,alpha,beta
                G1,1,10
                G2,2,20
                G3,3,30
            """),
            "statistics": {
                "histogram_alpha.json": json.dumps({
                    "bars": [1, 1, 1],
                    "bins": [1.0, 1.665, 2.333, 3.0],
                    "config": {
                        "type": "number",
                        "number_of_bins": 3,
                        "view_range": {"min": 1.0, "max": 3.0},
                        "x_log_scale": False,
                        "y_log_scale": False,
                    },
                }),
                "histogram_beta.json": json.dumps({
                    "bars": [1, 1, 1],
                    "bins": [10.0, 16.65, 23.33, 30.0],
                    "config": {
                        "type": "number",
                        "number_of_bins": 3,
                        "view_range": {"min": 10.0, "max": 30.0},
                        "x_log_scale": False,
                        "y_log_scale": False,
                    },
                }),
            },
        },
    })
    res = repo.get_resource("MultiScore")
    impl = GeneScoreImplementation(res)
    tasks = impl.create_statistics_build_tasks()
    assert len(tasks) == 1


# _calc_histogram tests (number and categorical)

def test_calc_histogram_number(inmemory_repo: GenomicResourceRepo) -> None:
    res = inmemory_repo.get_resource("LinearScore")
    histogram = GeneScoreImplementation._build_histograms(res)["score1"]
    assert isinstance(histogram, NumberHistogram)
    assert histogram.min_value == 1.0
    assert histogram.max_value == 3.0


def test_calc_histogram_categorical() -> None:
    repo = build_inmemory_test_repository({
        "CatScore": {
            GR_CONF_FILE_NAME: textwrap.dedent("""
                type: gene_score
                filename: cat.csv
                scores:
                - id: cat
                  desc: categorical
                  histogram:
                    type: categorical
                    value_order: [1, 2, 3]
            """),
            "cat.csv": textwrap.dedent("""
                gene,cat
                G1,1
                G2,2
                G3,3
                G4,1
            """),
            "statistics": {
                "histogram_cat.json": json.dumps({
                    "config": {
                        "type": "categorical",
                        "value_order": [1, 2, 3],
                        "y_log_scale": False,
                        "label_rotation": 0,
                    },
                    "values": {"1": 2, "2": 1, "3": 1},
                }),
            },
        },
    })
    res = repo.get_resource("CatScore")
    histogram = GeneScoreImplementation._build_histograms(res)["cat"]
    assert isinstance(histogram, CategoricalHistogram)
    assert histogram.raw_values[1] == 2
    assert histogram.raw_values[2] == 1
    assert histogram.raw_values[3] == 1


# ---------------------------------------------------------------------------
# _save_histogram (requires writable filesystem repo)
# ---------------------------------------------------------------------------

def test_save_histogram_writes_json_file(
    fs_repo: GenomicResourceRepo,
    tmp_path: pathlib.Path,
) -> None:
    res = fs_repo.get_resource("LinearScore")
    GeneScoreImplementation._build_histograms(res)

    hist_path = (
        tmp_path / "LinearScore" / "statistics" / "histogram_score1.json"
    )
    assert hist_path.exists()
    content = json.loads(hist_path.read_text())
    assert "config" in content
    assert "bars" in content


def test_save_histogram_writes_png_image(
    fs_repo: GenomicResourceRepo,
    tmp_path: pathlib.Path,
) -> None:
    res = fs_repo.get_resource("LinearScore")
    GeneScoreImplementation._build_histograms(res)

    png_path = tmp_path / "LinearScore" / "statistics" / "histogram_score1.png"
    assert png_path.exists()
    assert png_path.stat().st_size > 0


# ---------------------------------------------------------------------------
# calc_statistics_hash
# ---------------------------------------------------------------------------

def test_calc_statistics_hash_is_json(
    linear_impl: GeneScoreImplementation,
) -> None:
    result = linear_impl.calc_statistics_hash()
    assert isinstance(result, bytes)
    parsed = json.loads(result.decode())
    assert "score_config" in parsed
    assert "score_file" in parsed


def test_calc_statistics_hash_score_config_contains_score_id(
    linear_impl: GeneScoreImplementation,
) -> None:
    parsed = json.loads(linear_impl.calc_statistics_hash().decode())
    ids = [entry["id"] for entry in parsed["score_config"]]
    assert "score1" in ids


def test_calc_statistics_hash_changes_when_data_changes() -> None:
    def make_repo(val: str) -> GenomicResourceRepo:
        return build_inmemory_test_repository({
            "S": {
                GR_CONF_FILE_NAME: textwrap.dedent("""
                    type: gene_score
                    filename: s.csv
                    scores:
                    - id: s
                      desc: score
                      histogram:
                        type: number
                        number_of_bins: 3
                        x_log_scale: false
                        y_log_scale: false
                """),
                "s.csv": f"gene,s\nG1,{val}\nG2,2\n",
                "statistics": {
                    "histogram_s.json": json.dumps({
                        "bars": [1, 1],
                        "bins": [1.0, 1.5, 2.0],
                        "config": {
                            "type": "number",
                            "number_of_bins": 2,
                            "view_range": {"min": 1.0, "max": 2.0},
                            "x_log_scale": False,
                            "y_log_scale": False,
                        },
                    }),
                },
            },
        })

    impl1 = GeneScoreImplementation(make_repo("1").get_resource("S"))
    impl2 = GeneScoreImplementation(make_repo("99").get_resource("S"))
    assert impl1.calc_statistics_hash() != impl2.calc_statistics_hash()


def test_calc_statistics_hash_deterministic(
    inmemory_repo: GenomicResourceRepo,
) -> None:
    res = inmemory_repo.get_resource("LinearScore")
    impl = GeneScoreImplementation(res)
    assert impl.calc_statistics_hash() == impl.calc_statistics_hash()


# ---------------------------------------------------------------------------
# calc_info_hash
# ---------------------------------------------------------------------------

def test_calc_info_hash(linear_impl: GeneScoreImplementation) -> None:
    assert linear_impl.calc_info_hash() == b"placeholder"
