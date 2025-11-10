# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import cast

import pytest
from dae.genomic_resources.fsspec_protocol import FsspecReadOnlyProtocol
from dae.genomic_resources.group_repository import GenomicResourceGroupRepo
from dae.genomic_resources.repository import GenomicResourceProtocolRepo
from dae.genomic_resources.testing import build_inmemory_test_repository


@pytest.fixture
def group_repo() -> GenomicResourceGroupRepo:
    return GenomicResourceGroupRepo(children=[
        build_inmemory_test_repository(
            {
                "one": {"genomic_resource.yaml": ""},
            }),
        build_inmemory_test_repository(
            {
                "one(1.0)": {"genomic_resource.yaml": ""},
            }),
    ])


@pytest.fixture
def multi_resource_group() -> GenomicResourceGroupRepo:
    return GenomicResourceGroupRepo(
        children=[
            build_inmemory_test_repository({
                "res_a": {"genomic_resource.yaml": ""},
                "res_b(2.0)": {"genomic_resource.yaml": ""},
            }),
            build_inmemory_test_repository({
                "res_b": {"genomic_resource.yaml": ""},
                "res_c(1.5)": {"genomic_resource.yaml": ""},
            }),
            build_inmemory_test_repository({
                "res_c": {"genomic_resource.yaml": ""},
                "res_d": {"genomic_resource.yaml": ""},
            }),
        ],
        repo_id="multi_group",
    )


def test_lookup_priority_in_a_group_repository(
        group_repo: GenomicResourceGroupRepo) -> None:
    res = group_repo.get_resource("one")
    assert res
    assert res.resource_id == "one"
    assert res.version == (0,)
    assert res.proto is not None
    assert res.proto.get_id() == \
        cast(GenomicResourceProtocolRepo, group_repo.children[0])\
        .proto.get_id()


def test_lookup_in_a_group_repository_with_version_requirement(
        group_repo: GenomicResourceGroupRepo) -> None:
    res = group_repo.get_resource("one", version_constraint="1.0")
    assert res
    assert res.resource_id == "one"
    assert res.version == (1, 0)
    assert res.proto.get_id() == \
        cast(GenomicResourceProtocolRepo, group_repo.children[1])\
        .proto.get_id()


def test_group_repo_init_default_id() -> None:
    repo = GenomicResourceGroupRepo(children=[])
    assert repo.repo_id == "group_repo"


def test_group_repo_init_custom_id() -> None:
    repo = GenomicResourceGroupRepo(children=[], repo_id="custom_id")
    assert repo.repo_id == "custom_id"


def test_invalidate_propagates_to_children(
    multi_resource_group: GenomicResourceGroupRepo,
) -> None:
    # Access resources to populate caches
    list(multi_resource_group.get_all_resources())

    for child in multi_resource_group.children:
        proto_repo = cast(GenomicResourceProtocolRepo, child)
        assert cast(
            FsspecReadOnlyProtocol,
            proto_repo.proto,
        )._all_resources is not None

    multi_resource_group.invalidate()

    for child in multi_resource_group.children:
        proto_repo = cast(GenomicResourceProtocolRepo, child)
        assert cast(
            FsspecReadOnlyProtocol,
            proto_repo.proto,
        )._all_resources is None


def test_get_all_resources_from_multiple_repos(
    multi_resource_group: GenomicResourceGroupRepo,
) -> None:
    resources = list(multi_resource_group.get_all_resources())

    resource_ids = {res.resource_id for res in resources}
    assert resource_ids == {"res_a", "res_b", "res_c", "res_d"}

    # Check that we get multiple versions where present
    res_b_versions = [
        res.version for res in resources if res.resource_id == "res_b"
    ]
    assert (2, 0) in res_b_versions
    assert (0,) in res_b_versions


def test_find_resource_not_found() -> None:
    repo = GenomicResourceGroupRepo(
        children=[
            build_inmemory_test_repository({
                "exists": {"genomic_resource.yaml": ""},
            }),
        ],
    )

    result = repo.find_resource("nonexistent")
    assert result is None


def test_find_resource_with_version_not_found(
    group_repo: GenomicResourceGroupRepo,
) -> None:
    result = group_repo.find_resource("one", version_constraint=">=2.0")
    assert result is None


def test_get_resource_not_found_raises() -> None:
    repo = GenomicResourceGroupRepo(
        children=[
            build_inmemory_test_repository({
                "exists": {"genomic_resource.yaml": ""},
            }),
        ],
    )

    with pytest.raises(ValueError, match=r"resource nonexistent .* not found"):
        repo.get_resource("nonexistent")


def test_get_resource_first_child_takes_priority(
    multi_resource_group: GenomicResourceGroupRepo,
) -> None:
    # res_b exists in first child (v2.0) and second child (v0)
    res = multi_resource_group.get_resource("res_b")

    assert res.resource_id == "res_b"
    # Should get first child's version (2.0) when no version constraint
    assert res.version == (2, 0)


def test_empty_group_repo_get_all_resources() -> None:
    repo = GenomicResourceGroupRepo(children=[])
    resources = list(repo.get_all_resources())
    assert len(resources) == 0


def test_empty_group_repo_find_resource() -> None:
    repo = GenomicResourceGroupRepo(children=[])
    result = repo.find_resource("any")
    assert result is None


def test_get_resource_with_version_constraint_across_repos(
    multi_resource_group: GenomicResourceGroupRepo,
) -> None:
    # res_c exists as v1.5 in second child and v0 in third child
    res = multi_resource_group.get_resource("res_c", version_constraint=">=1.0")

    assert res.resource_id == "res_c"
    assert res.version == (1, 5)


def test_find_resource_returns_first_match() -> None:
    repo = GenomicResourceGroupRepo(
        children=[
            build_inmemory_test_repository(
                {"shared": {"genomic_resource.yaml": ""}},
            ),
            build_inmemory_test_repository(
                {"shared": {"genomic_resource.yaml": ""}},
            ),
        ],
    )

    res = repo.find_resource("shared")
    assert res is not None
    # Should return resource from first child
    assert res.version == (0,)


def test_get_all_resources_preserves_order() -> None:
    repo = GenomicResourceGroupRepo(
        children=[
            build_inmemory_test_repository({
                "first": {"genomic_resource.yaml": ""},
            }),
            build_inmemory_test_repository({
                "second": {"genomic_resource.yaml": ""},
            }),
            build_inmemory_test_repository({
                "third": {"genomic_resource.yaml": ""},
            }),
        ],
    )

    resources = list(repo.get_all_resources())
    resource_ids = [res.resource_id for res in resources]
    assert resource_ids == ["first", "second", "third"]


def test_find_resource_with_exact_version_match() -> None:
    repo = GenomicResourceGroupRepo(
        children=[
            build_inmemory_test_repository({
                "resource(1.0)": {"genomic_resource.yaml": ""},
            }),
            build_inmemory_test_repository({
                "resource(2.0)": {"genomic_resource.yaml": ""},
            }),
        ],
    )

    res = repo.find_resource("resource", version_constraint="=2.0")
    assert res is not None
    assert res.version == (2, 0)


def test_get_resource_with_version_not_in_first_child() -> None:
    repo = GenomicResourceGroupRepo(
        children=[
            build_inmemory_test_repository({
                "resource": {"genomic_resource.yaml": ""},
            }),
            build_inmemory_test_repository({
                "resource(1.5)": {"genomic_resource.yaml": ""},
            }),
        ],
    )

    # First child has v0, second has v1.5
    res = repo.get_resource("resource", version_constraint=">=1.0")
    assert res.version == (1, 5)


def test_invalidate_clears_resource_cache() -> None:
    repo = GenomicResourceGroupRepo(
        children=[
            build_inmemory_test_repository({
                "test": {"genomic_resource.yaml": ""},
            }),
        ],
    )

    # Populate cache
    _ = list(repo.get_all_resources())

    # Verify child has cached resources
    child = cast(GenomicResourceProtocolRepo, repo.children[0])
    assert cast(
            FsspecReadOnlyProtocol,
            child.proto,
        )._all_resources is not None

    # Invalidate
    repo.invalidate()

    # Verify cache is cleared
    assert cast(
            FsspecReadOnlyProtocol,
            child.proto,
        )._all_resources is None


def test_multiple_versions_same_resource_across_repos(
    multi_resource_group: GenomicResourceGroupRepo,
) -> None:
    # res_b has versions 2.0 and 0 across different children
    resources = [
        res for res in multi_resource_group.get_all_resources()
        if res.resource_id == "res_b"
    ]

    assert len(resources) == 2
    versions = {res.version for res in resources}
    assert versions == {(2, 0), (0,)}
