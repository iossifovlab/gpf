# pylint: disable=W0621,C0114,C0116,W0212,W0613
"""Expanded tests for annotation_pipeline_impl module."""
import pathlib
from unittest.mock import Mock, patch

import pytest
from dae.genomic_resources.genomic_scores import build_score_from_resource
from dae.genomic_resources.implementations.annotation_pipeline_impl import (
    AnnotationPipelineImplementation,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    setup_directories,
)
from dae.task_graph.graph import TaskGraph


@pytest.fixture
def grr_fixture(tmp_path: pathlib.Path) -> GenomicResourceRepo:
    """Create test repository with score and pipeline resources."""
    root_path = tmp_path / "grr"
    setup_directories(root_path, {
        "one": {
            "genomic_resource.yaml": """
                type: position_score
                table:
                    filename: data.txt
                scores:
                - id: score
                  type: float
                  desc: |
                      A score description testtest
                  name: s1
            """,
            "data.txt": "chrom\tpos_begin\tscore\n1\t100\t0.5\n",
        },
        "two": {
            "genomic_resource.yaml": """
                type: position_score
                table:
                    filename: data.txt
                scores:
                - id: score2
                  type: float
                  desc: Another score
                  name: s2
            """,
            "data.txt": "chrom\tpos_begin\tscore2\n1\t100\t0.8\n",
        },
        "pipeline": {
            "genomic_resource.yaml": """
                type: annotation_pipeline
                filename: annotation.yaml
            """,
            "annotation.yaml": """
                - position_score: one
            """,
        },
        "multi_pipeline": {
            "genomic_resource.yaml": """
                type: annotation_pipeline
                filename: annotation.yaml
            """,
            "annotation.yaml": """
                - position_score: one
                - position_score: two
            """,
        },
        "nested/deep/pipeline": {
            "genomic_resource.yaml": """
                type: annotation_pipeline
                filename: config.yaml
            """,
            "config.yaml": """
                - position_score: one
            """,
        },
    })
    return build_filesystem_test_repository(root_path)


@pytest.fixture
def alt_grr_fixture(tmp_path: pathlib.Path) -> GenomicResourceRepo:
    """Create alternative test repository."""
    root_path = tmp_path / "alt_grr"
    setup_directories(root_path, {
        "other_score": {
            "genomic_resource.yaml": """
                type: position_score
                table:
                    filename: data.txt
                scores:
                - id: score
                  type: float
                  name: s1
            """,
            "data.txt": "chrom\tpos_begin\tscore\n1\t100\t0.3\n",
        },
    })
    return build_filesystem_test_repository(root_path)


@pytest.fixture
def wrong_type_resource(tmp_path: pathlib.Path) -> GenomicResourceRepo:
    """Create repository with wrong resource type."""
    root_path = tmp_path / "wrong"
    setup_directories(root_path, {
        "genome": {
            "genomic_resource.yaml": """
                type: genome
                filename: genome.fa
            """,
            "genome.fa": ">chr1\nACGT\n",
        },
    })
    return build_filesystem_test_repository(root_path)


# Tests for __init__


def test_init_success(grr_fixture: GenomicResourceRepo) -> None:
    """Test successful initialization."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    assert impl is not None
    assert impl.pipeline is None  # Not loaded until get_info called
    assert impl.raw is not None


def test_init_wrong_resource_type(
    wrong_type_resource: GenomicResourceRepo,
) -> None:
    """Test initialization fails with wrong resource type."""
    with pytest.raises(ValueError, match="wrong resource type"):
        AnnotationPipelineImplementation(
            wrong_type_resource.get_resource("genome"),
        )


def test_init_loads_raw_config(grr_fixture: GenomicResourceRepo) -> None:
    """Test that raw config is loaded during init."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    assert "position_score: one" in impl.raw


# Tests for get_info


def test_get_info_basic(grr_fixture: GenomicResourceRepo) -> None:
    """Test basic get_info functionality."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    info = impl.get_info(repo=grr_fixture)
    assert info
    assert isinstance(info, str)


def test_get_info_contains_annotator_info(
    grr_fixture: GenomicResourceRepo,
) -> None:
    """Test that info contains annotator information."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    info = impl.get_info(repo=grr_fixture)
    assert "position_score" in info
    assert "one" in info


def test_get_info_contains_score_description(
    grr_fixture: GenomicResourceRepo,
) -> None:
    """Test that info contains score descriptions."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    info = impl.get_info(repo=grr_fixture)
    assert "A score description testtest" in info


def test_get_info_loads_pipeline(grr_fixture: GenomicResourceRepo) -> None:
    """Test that get_info loads the pipeline."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    assert impl.pipeline is None
    impl.get_info(repo=grr_fixture)
    assert impl.pipeline is not None


def test_get_info_multiple_annotators(
    grr_fixture: GenomicResourceRepo,
) -> None:
    """Test get_info with multiple annotators."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("multi_pipeline"),
    )
    info = impl.get_info(repo=grr_fixture)
    assert "one" in info
    assert "two" in info


# Tests for get_statistics_info


def test_get_statistics_info_basic(
    grr_fixture: GenomicResourceRepo,
) -> None:
    """Test basic get_statistics_info functionality."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    stats_info = impl.get_statistics_info(repo=grr_fixture)
    assert stats_info
    assert isinstance(stats_info, str)


def test_get_statistics_info_loads_pipeline(
    grr_fixture: GenomicResourceRepo,
) -> None:
    """Test that get_statistics_info loads the pipeline."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    assert impl.pipeline is None
    impl.get_statistics_info(repo=grr_fixture)
    assert impl.pipeline is not None


# Tests for get_template


def test_get_template(grr_fixture: GenomicResourceRepo) -> None:
    """Test get_template returns a Template object."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    template = impl.get_template()
    assert template is not None


def test_get_template_structure(grr_fixture: GenomicResourceRepo) -> None:
    """Test template has expected structure."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    template = impl.get_template()
    # Jinja2 Template objects can be rendered
    # Let's just verify it's callable/renderable
    assert hasattr(template, "render")


# Tests for _relative_prefix_to_root_dir


def test_relative_prefix_top_level(
    grr_fixture: GenomicResourceRepo,
) -> None:
    """Test relative prefix for top-level resource."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    assert impl._relative_prefix_to_root_dir == ".."


def test_relative_prefix_nested(grr_fixture: GenomicResourceRepo) -> None:
    """Test relative prefix for nested resource."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("nested/deep/pipeline"),
    )
    # nested/deep/pipeline has 3 levels, so needs ../../..
    assert impl._relative_prefix_to_root_dir == "../../.."


# Tests for _make_resource_url


def test_make_resource_url_same_repo(
    grr_fixture: GenomicResourceRepo,
) -> None:
    """Test URL generation for resource in same repository."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    res = grr_fixture.get_resource("one")
    url = impl._make_resource_url(res)
    assert url == "../one"


def test_make_resource_url_external_repo(
    grr_fixture: GenomicResourceRepo,
    alt_grr_fixture: GenomicResourceRepo,
) -> None:
    """Test URL generation for resource in different repository."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    other_res = alt_grr_fixture.get_resource("other_score")
    url = impl._make_resource_url(other_res)
    # Should return the full URL for external resources
    assert url == other_res.get_url()


def test_make_resource_url_nested_resource(
    grr_fixture: GenomicResourceRepo,
) -> None:
    """Test URL generation for nested resource."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("nested/deep/pipeline"),
    )
    res = grr_fixture.get_resource("one")
    url = impl._make_resource_url(res)
    assert url == "../../../one"


def test_make_resource_url_logs_warning_for_external(
    grr_fixture: GenomicResourceRepo,
    alt_grr_fixture: GenomicResourceRepo,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that warning is logged for external resources."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    other_res = alt_grr_fixture.get_resource("other_score")
    impl._make_resource_url(other_res)
    assert "Referencing resource outside managed GRR" in caplog.text


# Tests for _make_histogram_url


def test_make_histogram_url_same_repo(
    grr_fixture: GenomicResourceRepo,
) -> None:
    """Test histogram URL generation for same repository."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    score = build_score_from_resource(grr_fixture.get_resource("one"))
    url = impl._make_histogram_url(score, "s1")
    assert url == "../one/statistics/histogram_s1.png"


def test_make_histogram_url_external_repo(
    grr_fixture: GenomicResourceRepo,
    alt_grr_fixture: GenomicResourceRepo,
) -> None:
    """Test histogram URL generation for external repository."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    other_score = build_score_from_resource(
        alt_grr_fixture.get_resource("other_score"),
    )
    url = impl._make_histogram_url(other_score, "s1")
    assert url == other_score.get_histogram_image_url("s1")


def test_make_histogram_url_none_when_no_histogram(
    grr_fixture: GenomicResourceRepo,
) -> None:
    """Test histogram URL returns None when histogram doesn't exist."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    score = build_score_from_resource(grr_fixture.get_resource("one"))

    # Mock the histogram URL to return None
    with patch.object(
        score, "get_histogram_image_url", return_value=None,
    ):
        url = impl._make_histogram_url(score, "nonexistent")
        assert url is None


def test_make_histogram_url_nested_pipeline(
    grr_fixture: GenomicResourceRepo,
) -> None:
    """Test histogram URL for nested pipeline resource."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("nested/deep/pipeline"),
    )
    score = build_score_from_resource(grr_fixture.get_resource("one"))
    url = impl._make_histogram_url(score, "s1")
    assert url == "../../../one/statistics/histogram_s1.png"


def test_make_histogram_url_logs_warning_for_external(
    grr_fixture: GenomicResourceRepo,
    alt_grr_fixture: GenomicResourceRepo,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that warning is logged for external histogram."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    other_score = build_score_from_resource(
        alt_grr_fixture.get_resource("other_score"),
    )
    impl._make_histogram_url(other_score, "s1")
    assert "Referencing resource outside managed GRR" in caplog.text


# Tests for _get_template_data


def test_get_template_data_raises_without_pipeline(
    grr_fixture: GenomicResourceRepo,
) -> None:
    """Test _get_template_data raises ValueError without loaded pipeline."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    # The actual error has no message, so we verify it's a ValueError
    # by catching any ValueError type
    with pytest.raises(ValueError):  # noqa: PT011
        impl._get_template_data()


def test_get_template_data_with_loaded_pipeline(
    grr_fixture: GenomicResourceRepo,
) -> None:
    """Test _get_template_data returns data when pipeline is loaded."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    impl.get_info(repo=grr_fixture)  # This loads the pipeline
    data = impl._get_template_data()
    assert "content" in data
    assert isinstance(data["content"], str)


def test_get_template_data_content_structure(
    grr_fixture: GenomicResourceRepo,
) -> None:
    """Test that template data content has expected information."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    impl.get_info(repo=grr_fixture)
    data = impl._get_template_data()
    content = data["content"]
    # The content should contain information about the pipeline
    assert len(content) > 0


# Tests for files property


def test_files_property(grr_fixture: GenomicResourceRepo) -> None:
    """Test files property returns config filename."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    files = impl.files
    assert files == {"annotation.yaml"}


def test_files_property_different_filename(
    grr_fixture: GenomicResourceRepo,
) -> None:
    """Test files property with different config filename."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("nested/deep/pipeline"),
    )
    files = impl.files
    assert files == {"config.yaml"}


# Tests for calc_statistics_hash


def test_calc_statistics_hash(grr_fixture: GenomicResourceRepo) -> None:
    """Test calc_statistics_hash returns bytes."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    hash_val = impl.calc_statistics_hash()
    assert isinstance(hash_val, bytes)
    assert hash_val == b"placeholder"


# Tests for calc_info_hash


def test_calc_info_hash(grr_fixture: GenomicResourceRepo) -> None:
    """Test calc_info_hash returns bytes."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    hash_val = impl.calc_info_hash()
    assert isinstance(hash_val, bytes)
    assert hash_val == b"placeholder"


# Tests for add_statistics_build_tasks


def test_add_statistics_build_tasks_returns_empty_list(
    grr_fixture: GenomicResourceRepo,
) -> None:
    """Test add_statistics_build_tasks returns empty list."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    task_graph = Mock(spec=TaskGraph)
    tasks = impl.add_statistics_build_tasks(task_graph)
    assert not tasks


def test_add_statistics_build_tasks_with_kwargs(
    grr_fixture: GenomicResourceRepo,
) -> None:
    """Test add_statistics_build_tasks ignores kwargs."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )
    task_graph = Mock(spec=TaskGraph)
    tasks = impl.add_statistics_build_tasks(
        task_graph,
        some_arg="value",
        another_arg=123,
    )
    assert not tasks


# Integration tests


def test_full_workflow(grr_fixture: GenomicResourceRepo) -> None:
    """Test full workflow from init to getting info."""
    # Create implementation
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )

    # Verify initial state
    assert impl.pipeline is None
    assert impl.raw is not None

    # Get info
    info = impl.get_info(repo=grr_fixture)

    # Verify pipeline loaded
    assert impl.pipeline is not None
    assert info is not None
    assert "position_score" in info

    # Get template data
    data = impl._get_template_data()
    assert "content" in data


def test_multiple_calls_to_get_info(
    grr_fixture: GenomicResourceRepo,
) -> None:
    """Test that multiple calls to get_info work correctly."""
    impl = AnnotationPipelineImplementation(
        grr_fixture.get_resource("pipeline"),
    )

    info1 = impl.get_info(repo=grr_fixture)
    info2 = impl.get_info(repo=grr_fixture)

    # Should return consistent results
    assert info1 == info2
    assert impl.pipeline is not None
