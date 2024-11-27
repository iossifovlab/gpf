# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import yaml

from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.cached_repository import GenomicResourceCachedRepo
from dae.genomic_resources.fsspec_protocol import (
    FsspecRepositoryProtocol,
)
from dae.genomic_resources.genomic_scores import PositionScore
from dae.genomic_resources.group_repository import GenomicResourceGroupRepo
from dae.genomic_resources.repository import (
    GenomicResourceProtocolRepo,
)


def test_build_an_empty_repository() -> None:
    empty_repository = build_genomic_resource_repository(
        {"id": "empty", "type": "embedded", "content": {}})
    assert len(list(empty_repository.get_all_resources())) == 0


def test_build_a_repository_with_one_resource() -> None:
    one_resrouce_repo = build_genomic_resource_repository(
        {"id": "oneResrouce",
         "type": "embedded",
         "content": {
                 "one": {"genomic_resource.yaml": ""},
         },
         })
    assert len(list(one_resrouce_repo.get_all_resources())) == 1


def test_build_a_group_repository() -> None:
    repo = build_genomic_resource_repository(
        {"type": "group", "children": [
            {"id": "a", "type": "embedded", "content": {}},
            {"id": "b", "type": "embedded", "content": {}},
        ]})
    assert isinstance(repo, GenomicResourceGroupRepo)
    assert len(repo.children) == 2


def test_build_a_complex_but_realistic_scenario(
    tmp_path: pathlib.Path,
) -> None:
    repo = build_genomic_resource_repository(
        {"type": "group", "children": [
            {
                "type": "group",
                "cache_dir": tmp_path / "ttt/remotes12Cache", "children": [
                    {"id": "r1", "type": "http", "url": "http://r1.org/repo"},
                    {"id": "r2", "type": "http", "url": "http://r2.org/repo"},
                ]},
            {"id": "r3", "type": "http", "url": "http://r3.org/repo",
             "cache_dir": tmp_path / "ttt/remote3Cache"},
            {"id": "my", "type": "directory",
             "directory": tmp_path / "data/my/grRepo"},
            {"id": "mm", "type": "embedded", "content": {}},
        ]})
    # The asserts implicitly test the types of the repositories too:
    #   * only group     repository has a 'children'              attribute;
    #   * only chached   repository has a 'child' and 'cache_dir' attributes;
    #   * only url       repository has a 'url'                   attribute;
    #   * only directory repository has a 'directory'             attribute;
    #   * only embedded   repository has a 'content'               attribute.

    assert isinstance(repo, GenomicResourceGroupRepo)

    assert isinstance(repo.children[0], GenomicResourceCachedRepo)
    assert str(repo.children[0].cache_url) == \
        f"file://{tmp_path / 'ttt/remotes12Cache'!s}"

    assert isinstance(repo.children[0].child, GenomicResourceGroupRepo)
    assert isinstance(
        repo.children[0].child.children[0],
        GenomicResourceProtocolRepo)
    assert repo.children[0].child.children[0].proto.url == \
        "http://r1.org/repo"

    assert isinstance(
        repo.children[0].child.children[1],
        GenomicResourceProtocolRepo)
    assert repo.children[0].child.children[1].proto.url == \
        "http://r2.org/repo"

    assert isinstance(repo.children[1], GenomicResourceCachedRepo)
    assert str(repo.children[1].cache_url) == \
        f"file://{tmp_path / 'ttt/remote3Cache'!s}"

    assert isinstance(
        repo.children[1].child,
        GenomicResourceProtocolRepo)
    assert repo.children[1].child.proto.url == "http://r3.org/repo"

    assert isinstance(
        repo.children[2],
        GenomicResourceProtocolRepo)
    assert repo.children[2].proto.url == \
        f"file://{tmp_path / 'data/my/grRepo'!s}"

    assert isinstance(
        repo.children[3],
        GenomicResourceProtocolRepo)
    assert isinstance(
        repo.children[3].proto,
        FsspecRepositoryProtocol)
    assert repo.children[3].proto.scheme == "memory"


def test_build_a_complex_but_realistic_scenario_yaml(
    tmp_path: pathlib.Path,
) -> None:
    definition = yaml.safe_load(f"""
        type: group
        children:
        - type: group
          cache_dir: "{tmp_path!s}/ttt/remotes12Cache(1.3)"
          children:
          - id: r1
            type: http
            url: http://r1.org/repo
          - id: r2
            type: http
            url: http://r2.org/repo
        - id: r3
          type: http
          url: http://r3.org/repo
          cache_dir: {tmp_path!s}/ttt/remote3Cache
        - id: my
          type: directory
          directory: {tmp_path!s}/data/my/grRepo
        - id: mm
          type: embedded
          content: {{}}

    """)
    repo = build_genomic_resource_repository(definition)

    # The asserts implicitly test the types of the repositories too:
    #   * only group     repository has a 'children'              attribute;
    #   * only chached   repository has a 'child' and 'cache_dir' attributes;
    #   * only url       repository has a 'url'                   attribute;
    #   * only directory repository has a 'directory'             attribute;
    #   * only embedded   repository has a 'content'               attribute.
    assert isinstance(repo, GenomicResourceGroupRepo)

    assert isinstance(repo.children[0], GenomicResourceCachedRepo)
    assert str(repo.children[0].cache_url) == \
        f"file://{tmp_path}/ttt/remotes12Cache(1.3)"

    assert isinstance(repo.children[0].child, GenomicResourceGroupRepo)
    assert isinstance(
        repo.children[0].child.children[0],
        GenomicResourceProtocolRepo)
    assert repo.children[0].child.children[0].proto.url == \
        "http://r1.org/repo"

    assert isinstance(
        repo.children[0].child.children[1],
        GenomicResourceProtocolRepo)
    assert repo.children[0].child.children[1].proto.url == \
        "http://r2.org/repo"

    assert isinstance(repo.children[1], GenomicResourceCachedRepo)
    assert str(repo.children[1].cache_url) == \
        f"file://{tmp_path}/ttt/remote3Cache"

    assert isinstance(
        repo.children[1].child,
        GenomicResourceProtocolRepo)
    assert repo.children[1].child.proto.url == "http://r3.org/repo"

    assert isinstance(
        repo.children[2],
        GenomicResourceProtocolRepo)
    assert repo.children[2].proto.url == f"file://{tmp_path}/data/my/grRepo"

    assert isinstance(
        repo.children[3],
        GenomicResourceProtocolRepo)
    assert isinstance(
        repo.children[3].proto,
        FsspecRepositoryProtocol)
    assert repo.children[3].proto.scheme == "memory"


def test_build_a_configuration_with_embedded() -> None:
    definition = yaml.safe_load("""
        id: mm
        type: embedded
        content:
            one:
                genomic_resource.yaml: |
                    type: position_score
                    table:
                        filename: data.mem
                    scores:
                    - id: score
                      type: float
                      desc: >
                            The phastCons computed over the tree of 100
                            verterbarte species
                      name: s1
                data.mem: |
                    chrom  pos_begin  s1
                    chr1   23         0.01
                    chr1   24         0.2""")
    repo = build_genomic_resource_repository(definition)
    assert repo is not None
    res = repo.get_resource("one")
    assert res is not None

    score = PositionScore(res)
    score.open()
    assert score.fetch_scores("chr1", 23) == [0.01]
