# pylint: disable=redefined-outer-name,C0114,C0116,protected-access

import pytest

from dae.genomic_resources.group_repository import GenomicResourceGroupRepo


@pytest.fixture
def group_repo(repo_testing):
    repo = GenomicResourceGroupRepo(children=[
        repo_testing(
            repo_id="a",
            scheme="memory",
            content={
                "one": {"genomic_resource.yaml": ""}
            }),
        repo_testing(
            repo_id="b",
            scheme="memory",
            content={
                "one(1.0)": {"genomic_resource.yaml": ""}
            })
    ])
    return repo


def test_lookup_priority_in_a_group_repository(group_repo):
    res = group_repo.get_resource("one")
    assert res
    assert res.resource_id == "one"
    assert res.version == (0,)
    assert res.proto.get_id() == "a"


def test_lookup_in_a_group_repository_with_version_requirement(group_repo):
    res = group_repo.get_resource("one", version_constraint="1.0")
    assert res
    assert res.resource_id == "one"
    assert res.version == (1, 0)
    assert res.proto.get_id() == "b"
