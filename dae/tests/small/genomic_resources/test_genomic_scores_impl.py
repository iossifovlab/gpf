# pylint: disable=W0621,C0114,C0116,W0212,W0613

import json
import pathlib
import textwrap
from typing import cast

from dae.genomic_resources.histogram import (
    CategoricalHistogramConfig,
    HistogramConfig,
    NullHistogramConfig,
    NumberHistogramConfig,
)
from dae.genomic_resources.implementations.genomic_scores_impl import (
    GenomicScoreImplementation,
    build_score_implementation_from_resource,
)
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.statistics.min_max import MinMaxValue
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    build_inmemory_test_resource,
    convert_to_tab_separated,
    setup_directories,
    setup_genome,
)
from dae.task_graph.graph import TaskGraph


def test_unpack_score_defs_classifies_histograms() -> None:
    res = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: float_score
                  name: float_score
                  type: float
                - id: str_score
                  name: str_score
                  type: str
                - id: null_score
                  name: null_score
                  type: float
                  histogram:
                    type: "null"
                    reason: disabled
                - id: preset_score
                  name: preset_score
                  type: float
                  histogram:
                    type: number
                    view_range:
                        min: 0.0
                        max: 1.0
        """,
        "data.mem": convert_to_tab_separated(
            """
            chrom pos_begin float_score str_score null_score preset_score
            1     10        0.1         A         0.9        0.5
            """,
        ),
    })

    (
        min_max_scores,
        hist_confs,
    ) = GenomicScoreImplementation._unpack_score_defs(res)

    assert min_max_scores == ["float_score"]
    assert isinstance(hist_confs["float_score"], NumberHistogramConfig)
    assert not hist_confs["float_score"].has_view_range()
    assert isinstance(hist_confs["str_score"], CategoricalHistogramConfig)
    assert isinstance(hist_confs["null_score"], NullHistogramConfig)
    preset_hist = cast(NumberHistogramConfig, hist_confs["preset_score"])
    assert preset_hist.view_range == (0.0, 1.0)


def test_update_hist_confs_sets_view_range() -> None:
    hist_confs = {"score": NumberHistogramConfig((None, None))}
    minmax = {"score": MinMaxValue("score", 1.0, 5.0)}

    result = GenomicScoreImplementation._update_hist_confs(
        cast(dict[str, HistogramConfig], hist_confs),
        minmax,
    )

    updated_hist = cast(NumberHistogramConfig, result["score"])
    assert updated_hist.view_range == (1.0, 5.0)


def test_update_hist_confs_nullifies_on_nan() -> None:
    hist_confs = {"score": NumberHistogramConfig((None, None))}
    minmax = {"score": MinMaxValue("score")}

    result = GenomicScoreImplementation._update_hist_confs(
        cast(dict[str, HistogramConfig], hist_confs),
        minmax,
    )

    assert isinstance(result["score"], NullHistogramConfig)


def test_get_reference_genome_cached(tmp_path: pathlib.Path) -> None:
    setup_directories(
        tmp_path,
        {
            "score": {
                "genomic_resource.yaml": textwrap.dedent(
                    """
                    type: position_score
                    table:
                        filename: data.txt
                    scores:
                        - id: value
                          name: value
                          type: float
                    meta:
                        labels:
                            reference_genome: ref
                    """,
                ),
                "data.txt": convert_to_tab_separated(
                    """
                    chrom pos_begin value
                    1     10        0.1
                    """,
                ),
            },
            "ref": {
                "genomic_resource.yaml": "{type: genome, filename: genome.fa}",
            },
        },
    )
    setup_genome(tmp_path / "ref" / "genome.fa", ">chr1\nAC\n")

    grr = build_filesystem_test_repository(tmp_path)

    GenomicScoreImplementation._REF_GENOME_CACHE.clear()
    ref = GenomicScoreImplementation._get_reference_genome_cached(grr, "ref")

    assert ref is not None
    assert "ref" in GenomicScoreImplementation._REF_GENOME_CACHE
    cached = GenomicScoreImplementation._get_reference_genome_cached(
        grr,
        "ref",
    )
    assert cached is ref
    assert (
        GenomicScoreImplementation._get_reference_genome_cached(None, "ref")
        is None
    )


def test_get_chrom_regions_region_size_zero() -> None:
    res = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: score
                  name: score
                  type: float
        """,
        "data.mem": convert_to_tab_separated(
            """
            chrom pos_begin score
            1     10        0.1
            """,
        ),
    })

    impl = build_score_implementation_from_resource(res)
    impl.score.open()
    regions = impl._get_chrom_regions(0)

    assert len(regions) == 1
    assert regions[0].chrom is None
    assert regions[0].start is None
    assert regions[0].stop is None


def test_add_statistics_build_tasks_creates_min_max_tasks() -> None:
    res = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: value
                  name: value
                  type: float
        """,
        "data.mem": convert_to_tab_separated(
            """
            chrom pos_begin value
            1     10        0.1
            1     11        0.2
            """,
        ),
    })

    impl = build_score_implementation_from_resource(res)
    graph = TaskGraph()

    tasks = impl.add_statistics_build_tasks(graph, region_size=0)

    assert len(tasks) == 1
    save_task = tasks[0]
    assert save_task.func is GenomicScoreImplementation._save_histograms

    task_ids = {task.task_id for task in graph.tasks}
    assert any("calculate_min_max" in task_id for task_id in task_ids)
    merge_task = next(
        task for task in graph.tasks if task.task_id.endswith("_merge_min_max")
    )
    update_task = next(
        task
        for task in graph.tasks
        if task.task_id.endswith("_update_hist_confs")
    )
    assert merge_task in update_task.deps


def test_add_statistics_tasks_skip_min_max_when_hist_has_range() -> None:
    res = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: value
                  name: value
                  type: float
                  histogram:
                    type: number
                    view_range:
                        min: 0.0
                        max: 1.0
        """,
        "data.mem": convert_to_tab_separated(
            """
            chrom pos_begin value
            1     10        0.1
            """,
        ),
    })

    impl = build_score_implementation_from_resource(res)
    graph = TaskGraph()

    impl.add_statistics_build_tasks(graph, region_size=0)

    task_ids = {task.task_id for task in graph.tasks}
    assert not any("merge_min_max" in task_id for task_id in task_ids)
    update_task = next(
        task
        for task in graph.tasks
        if task.task_id.endswith("_update_hist_confs")
    )
    assert update_task.deps == []


def test_add_min_max_tasks_builds_graph() -> None:
    res = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: value
                  name: value
                  type: float
        """,
        "data.mem": convert_to_tab_separated(
            """
            chrom pos_begin value
            1     10        0.1
            """,
        ),
    })

    impl = build_score_implementation_from_resource(res)
    graph = TaskGraph()

    calc_tasks, merge_task = impl._add_min_max_tasks(
        graph,
        ["value"],
        region_size=0,
    )

    assert len(calc_tasks) == 1
    calculate_task = calc_tasks[0]
    assert calculate_task.func is GenomicScoreImplementation._do_min_max
    assert merge_task.func is GenomicScoreImplementation._merge_min_max
    assert calculate_task in merge_task.deps


def test_add_histogram_tasks_skip_null_histograms_and_link_minmax() -> None:
    res = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: value
                  name: value
                  type: float
        """,
        "data.mem": convert_to_tab_separated(
            """
            chrom pos_begin value
            1     10        0.1
            """,
        ),
    })

    impl = build_score_implementation_from_resource(res)
    graph = TaskGraph()

    minmax_task = graph.create_task(
        "dummy_minmax",
        lambda: {"value": MinMaxValue("value", 0.1, 0.2)},
        args=[],
        deps=[],
    )

    hist_confs: dict[str, HistogramConfig] = {
        "value": NumberHistogramConfig((None, None)),
        "skip": NullHistogramConfig("disabled"),
    }

    histogram_tasks, merge_task, save_task = impl._add_histogram_tasks(
        graph,
        hist_confs,
        minmax_task,
        region_size=0,
    )

    assert len(histogram_tasks) == 1
    histogram_task = histogram_tasks[0]
    assert histogram_task.func is GenomicScoreImplementation._do_histogram

    update_task = next(
        task
        for task in graph.tasks
        if task.task_id.endswith("_update_hist_confs")
    )
    assert minmax_task in update_task.deps

    assert merge_task.func is GenomicScoreImplementation._merge_histograms
    assert histogram_task in merge_task.deps
    assert update_task in merge_task.deps

    assert save_task.func is GenomicScoreImplementation._save_histograms
    assert merge_task in save_task.deps


def test_calc_statistics_hash_includes_expected_fields() -> None:
    res = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: value
                  name: value
                  type: float
                  histogram:
                    type: number
                    view_range:
                        min: 0.0
                        max: 1.0
                - id: label
                  name: label
                  type: str
        """,
        "data.mem": convert_to_tab_separated(
            """
            chrom pos_begin value label
            1     10        0.1   A
            """,
        ),
    })

    impl = build_score_implementation_from_resource(res)

    blob = impl.calc_statistics_hash()
    payload = json.loads(blob.decode())

    # Table config and files md5 present
    assert payload["config"]["table"]["config"]["filename"] == "data.mem"
    files_md5 = payload["config"]["table"]["files_md5"]
    assert "data.mem" in files_md5
    assert isinstance(files_md5["data.mem"], str)
    assert len(files_md5["data.mem"]) > 0

    # Score configuration mirrors resource definitions
    score_ids = {s["id"] for s in payload["score_config"]}
    assert score_ids == {"value", "label"}


def test_calc_statistics_hash_changes_when_file_changes() -> None:
    res1 = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: value
                  name: value
                  type: float
        """,
        "data.mem": convert_to_tab_separated(
            """
            chrom pos_begin value
            1     10        0.1
            """,
        ),
    })
    res2 = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: value
                  name: value
                  type: float
        """,
        "data.mem": convert_to_tab_separated(
            """
            chrom pos_begin value
            1     10        0.2
            """,
        ),
    })

    impl1 = build_score_implementation_from_resource(res1)
    impl2 = build_score_implementation_from_resource(res2)

    h1 = impl1.calc_statistics_hash()
    h2 = impl2.calc_statistics_hash()

    assert h1 != h2


def test_calc_statistics_hash_deterministic_for_same_content() -> None:
    res_a = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: value
                  name: value
                  type: float
        """,
        "data.mem": convert_to_tab_separated(
            """
            chrom pos_begin value
            1     10        0.1
            """,
        ),
    })
    res_b = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: value
                  name: value
                  type: float
        """,
        "data.mem": convert_to_tab_separated(
            """
            chrom pos_begin value
            1     10        0.1
            """,
        ),
    })

    impl_a = build_score_implementation_from_resource(res_a)
    impl_b = build_score_implementation_from_resource(res_b)

    assert impl_a.calc_statistics_hash() == impl_b.calc_statistics_hash()
