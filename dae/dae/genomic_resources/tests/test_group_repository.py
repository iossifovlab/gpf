# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import cast

import pytest

from dae.genomic_resources.group_repository import GenomicResourceGroupRepo
from dae.genomic_resources.repository import GenomicResourceProtocolRepo
from dae.genomic_resources.testing import build_inmemory_test_repository


@pytest.fixture
def group_repo() -> GenomicResourceGroupRepo:
    repo = GenomicResourceGroupRepo(children=[
        build_inmemory_test_repository(
            {
                "one": {"genomic_resource.yaml": ""}
            }),
        build_inmemory_test_repository(
            {
                "one(1.0)": {"genomic_resource.yaml": ""}
            })
    ])
    return repo


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
