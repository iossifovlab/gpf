from dae.genomic_resources import build_genomic_resource_repository


def test_build_an_empty_repository():
    emptyRepository = build_genomic_resource_repository(
        {"id": "empty", "type": "embeded", "content": {}})
    assert len(list(emptyRepository.get_all_resources())) == 0


def test_build_a_repository_with_one_resource():
    oneResrouceRepo = build_genomic_resource_repository(
        {"id": "oneResrouce",
         "type": "embeded",
         "content": {
                 "one": {"genomic_resource.yaml": ""}
         }
         })
    assert len(list(oneResrouceRepo.get_all_resources())) == 1


def test_build_a_group_repository():
    repo = build_genomic_resource_repository(
        {"type": "group", "children": [
            {"id": "a", "type": "embeded", "content": {}},
            {"id": "b", "type": "embeded", "content": {}}
        ]})
    assert len(repo.children) == 2


def test_build_a_complex_but_realistic_scenario():
    repo = build_genomic_resource_repository(
        {"type": "group", "children": [
            {"type": "group", "cacheDir": "/tmp/remotes12Cache", "children": [
                {"id": "r1", "type": "url", "url": "http://r1.org/repo"},
                {"id": "r2", "type": "url", "url": "http://r2.org/repo"}
            ]},
            {"id": "r3", "type": "url", "url": "http://r3.org/repo",
             "cacheDir": "/tmp/remote3Cache"},
            {"id": "my", "type": "directory", "directory": "/data/my/grRepo"},
            {"id": "mm", "type": "embeded", "content": {}}
        ]})
    # The asserts implicitly test the types of the repositories too:
    #   * only group     repository has a 'children'             attribute;
    #   * only chached   repository has a 'child' and 'cacheDir' attributes;
    #   * only url       repository has a 'url'                  attribute;
    #   * only directory repository has a 'directory'            attribute;
    #   * only embeded   repository has a 'content'              attribute.
    assert str(repo.children[0].cacheDir) == "/tmp/remotes12Cache"
    assert repo.children[0].child.children[0].url == "http://r1.org/repo"
    assert repo.children[0].child.children[1].url == "http://r2.org/repo"
    assert str(repo.children[1].cacheDir) == "/tmp/remote3Cache"
    assert repo.children[1].child.url == "http://r3.org/repo"
    assert str(repo.children[2].directory) == "/data/my/grRepo"
    assert repo.children[3].content == {}


def test_build_a_complex_but_realistic_scenario_yaml():
    import yaml
    definition = yaml.safe_load('''
        {type: group, children: [
            {type: group, cacheDir: /tmp/remotes12Cache, children: [
                {id: r1, type: url, url: http://r1.org/repo},
                {id: r2, type: url, url: http://r2.org/repo},
            ]},
            {id: r3, type: url, url: http://r3.org/repo,
                                cacheDir: /tmp/remote3Cache},
            {id: my, type: directory, directory: /data/my/grRepo},
            {id: mm, type: embeded, content: {}}
        ]}
    ''')
    repo = build_genomic_resource_repository(definition)

    # The asserts implicitly test the types of the repositories too:
    #   * only group     repository has a 'children'             attribute;
    #   * only chached   repository has a 'child' and 'cacheDir' attributes;
    #   * only url       repository has a 'url'                  attribute;
    #   * only directory repository has a 'directory'            attribute;
    #   * only embeded   repository has a 'content'              attribute.
    assert str(repo.children[0].cacheDir) == "/tmp/remotes12Cache"
    assert repo.children[0].child.children[0].url == "http://r1.org/repo"
    assert repo.children[0].child.children[1].url == "http://r2.org/repo"
    assert str(repo.children[1].cacheDir) == "/tmp/remote3Cache"
    assert repo.children[1].child.url == "http://r3.org/repo"
    assert str(repo.children[2].directory) == "/data/my/grRepo"
    assert repo.children[3].content == {}
