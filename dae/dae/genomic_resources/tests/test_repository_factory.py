# pylint: disable=W0621,C0114,C0116,W0212,W0613

import yaml
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.genomic_scores import \
    build_position_score_from_resource


def test_build_an_empty_repository():
    empty_repository = build_genomic_resource_repository(
        {"id": "empty", "type": "embedded", "content": {}})
    assert len(list(empty_repository.get_all_resources())) == 0


def test_build_a_repository_with_one_resource():
    one_resrouce_repo = build_genomic_resource_repository(
        {"id": "oneResrouce",
         "type": "embedded",
         "content": {
                 "one": {"genomic_resource.yaml": ""}
         }
         })
    assert len(list(one_resrouce_repo.get_all_resources())) == 1


def test_build_a_group_repository():
    repo = build_genomic_resource_repository(
        {"type": "group", "children": [
            {"id": "a", "type": "embedded", "content": {}},
            {"id": "b", "type": "embedded", "content": {}}
        ]})
    assert len(repo.children) == 2


def test_build_a_complex_but_realistic_scenario(tmp_path):
    repo = build_genomic_resource_repository(
        {"type": "group", "children": [
            {
                "type": "group",
                "cache_dir": tmp_path / "tmp/remotes12Cache", "children": [
                    {"id": "r1", "type": "http", "url": "http://r1.org/repo"},
                    {"id": "r2", "type": "http", "url": "http://r2.org/repo"}
                ]},
            {"id": "r3", "type": "http", "url": "http://r3.org/repo",
             "cache_dir": tmp_path / "tmp/remote3Cache"},
            {"id": "my", "type": "directory",
             "directory": tmp_path / "data/my/grRepo"},
            {"id": "mm", "type": "embedded", "content": {}}
        ]})
    # The asserts implicitly test the types of the repositories too:
    #   * only group     repository has a 'children'              attribute;
    #   * only chached   repository has a 'child' and 'cache_dir' attributes;
    #   * only url       repository has a 'url'                   attribute;
    #   * only directory repository has a 'directory'             attribute;
    #   * only embedded   repository has a 'content'               attribute.

    assert str(repo.children[0].cache_url) == \
        f"file://{str(tmp_path / 'tmp/remotes12Cache')}"
    assert repo.children[0].child.children[0].proto.url == \
        "http://r1.org/repo"
    assert repo.children[0].child.children[1].proto.url == \
        "http://r2.org/repo"
    assert str(repo.children[1].cache_url) == \
        f"file://{str(tmp_path / 'tmp/remote3Cache')}"

    assert repo.children[1].child.proto.url == "http://r3.org/repo"
    assert repo.children[2].proto.url == \
        f"file://{str(tmp_path / 'data/my/grRepo')}"

    assert repo.children[3].proto.scheme == "memory"


def test_build_a_complex_but_realistic_scenario_yaml(tmp_path):
    definition = yaml.safe_load(f"""
        type: group
        children:
        - type: group
          cache_dir: "{str(tmp_path)}/tmp/remotes12Cache"
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
          cache_dir: {str(tmp_path)}/tmp/remote3Cache
        - id: my
          type: directory
          directory: {str(tmp_path)}/data/my/grRepo
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
    assert str(repo.children[0].cache_url) == \
        f"file://{tmp_path}/tmp/remotes12Cache"
    assert repo.children[0].child.children[0].proto.url == \
        "http://r1.org/repo"
    assert repo.children[0].child.children[1].proto.url == \
        "http://r2.org/repo"
    assert str(repo.children[1].cache_url) == \
        f"file://{tmp_path}/tmp/remote3Cache"
    assert repo.children[1].child.proto.url == "http://r3.org/repo"
    assert repo.children[2].proto.url == f"file://{tmp_path}/data/my/grRepo"
    assert repo.children[3].proto.scheme == "memory"


def test_build_a_configuration_with_embedded():
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

    score = build_position_score_from_resource(res)
    score.open()
    assert score.fetch_scores("chr1", 23) == {"score": 0.01}
