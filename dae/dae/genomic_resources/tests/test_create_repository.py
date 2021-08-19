import pytest
import os
import yaml

from urllib.parse import urlparse
from box import Box

from dae.genomic_resources.resources import GenomicResource, \
    GenomicResourceGroup
from dae.genomic_resources.repository import \
    _walk_genomic_resources_repository, \
    _walk_genomic_repository_content, \
    _create_genomic_resources_hierarchy, \
    _create_resource_content_dict, \
    create_fs_genomic_resource_repository, \
    GenomicResourcesRepo


class FakeRepository(GenomicResourcesRepo):

    def create_resource(self, resource_id, path):
        return GenomicResource(Box({"id": resource_id}), repo=self)


@pytest.fixture
def fake_repo():
    fake_repo = FakeRepository("fake_repo_id", "/repo/path")
    return fake_repo


def test_create_genomic_resources_hierarchy(fixture_dirname, fake_repo):
    repo_dirname = fixture_dirname("genomic_resources")
    print(repo_dirname)

    root_group = _create_genomic_resources_hierarchy(
        fake_repo,
        _walk_genomic_resources_repository(repo_dirname))
    assert root_group is not None

    res = root_group.get_resource("hg19/CADD")
    assert res is not None
    assert isinstance(res, GenomicResource)

    res = root_group.get_resource(
        "hg19/GATK_ResourceBundle_5777_b37_phiX174/genome")
    assert res is not None
    assert isinstance(res, GenomicResource)


def test_create_genomic_resource_hierarchy_good(fake_repo):
    root_group = _create_genomic_resources_hierarchy(
        fake_repo,
        [
            (("a", "b"), ("c", "c_path")),
            (("a", "b"), ("d", "d_path")),
        ]
    )
    res = root_group.get_resource("a/b/d")
    assert res is not None
    assert res.get_id() == "a/b/d"


def test_create_genomic_resource_hierarchy_bad_1(fake_repo):
    with pytest.raises(AssertionError):
        _create_genomic_resources_hierarchy(
            fake_repo,
            [
                (("a", "b"), ("c", "c_path")),
                (("a", "b", "c"), ("d", "d_path")),
            ]
        )


def test_create_genomic_resource_hierarchy_bad_2(fake_repo):
    with pytest.raises(AssertionError):
        _create_genomic_resources_hierarchy(
            fake_repo,
            [
                (("a", "b", "c"), ("d", "d_path")),
                (("a", "b"), ("c", "c_path")),
            ]
        )


def test_create_genomic_resource_hierarchy_bad_3(fake_repo):
    with pytest.raises(AssertionError):
        _create_genomic_resources_hierarchy(
            fake_repo,
            [
                (("a", "b"), ("c", "c_path")),
                (("a", "b"), ("c", "d_path")),
            ]
        )


def test_walk_genomic_resources_repository(fixture_dirname):
    repo_dirname = fixture_dirname("genomic_resources")
    print(repo_dirname)

    for parents, child, in _walk_genomic_resources_repository(repo_dirname):
        print(parents, child)


@pytest.fixture
def genomic_group():
    g1 = GenomicResourceGroup("a", "url1")
    g2 = GenomicResourceGroup("a/b", "url2")

    g1.add_child(g2)

    g3 = GenomicResourceGroup("a/b/c", "url3")
    g2.add_child(g3)

    print(g1.resource_children())

    r = GenomicResource(Box({"id": "a/b/c/d"}))
    g3.add_child(r)

    return g1


def test_group_resource_children(genomic_group):
    g1 = genomic_group

    print(g1.resource_children())

    children = g1.resource_children()

    assert len(children) == 1
    groups = children[0][0]
    res = children[0][1]

    assert res.get_id() == "a/b/c/d"
    assert len(groups) == 3


def test_group_resources(genomic_group):
    g1 = genomic_group
    print(g1.get_resources())

    assert len(g1.get_children()) == 1
    print(g1.get_children(deep=True))


def test_group_get_resource(genomic_group):
    assert genomic_group.get_id() == "a"

    res = genomic_group.get_resource("a/b")
    assert res is not None
    assert res.get_id() == "a/b"

    res = genomic_group.get_resource("a/b/c")
    assert res is not None
    assert res.get_id() == "a/b/c"

    res = genomic_group.get_resource("a/b/c/d")
    assert res is not None
    assert res.get_id() == "a/b/c/d"

    res = genomic_group.get_resource("d")
    assert res is None


@pytest.fixture
def root_group():
    g1 = GenomicResourceGroup("", "url1")
    g2 = GenomicResourceGroup("a", "url2")

    g1.add_child(g2)

    g3 = GenomicResourceGroup("a/b", "url3")
    g2.add_child(g3)

    print(g1.resource_children())

    r = GenomicResource(Box({"id": "a/b/c"}))
    g3.add_child(r)

    return g1


def test_root_group_get_resource(root_group):

    assert root_group.get_id() == ""

    res = root_group.get_resource("a/b")
    assert res is not None
    assert res.get_id() == "a/b"

    res = root_group.get_resource("a/b/c")
    assert res is not None
    assert res.get_id() == "a/b/c"

    res = root_group.get_resource("a/b/c/d")
    assert res is None


def test_root_group_get_resource_not_deep(root_group):

    assert root_group.get_id() == ""

    res = root_group.get_resource("a", deep=False)
    assert res is not None
    assert res.get_id() == "a"

    res = root_group.get_resource("a/b", deep=False)
    assert res is None

    res = root_group.get_resource("a/b", deep=True)
    assert res is not None
    assert res.get_id() == "a/b"


def test_create_resource_content_dict_group(root_group):
    res = root_group.get_resource("a/b", deep=True)
    section = _create_resource_content_dict(res)
    assert section is not None

    assert section["id"] == "a/b"
    assert section["type"] == "group"
    assert len(section["children"]) == 1


def test_create_resource_content_dict_resource(root_group):
    res = root_group.get_resource("a/b/c", deep=True)
    section = _create_resource_content_dict(res)
    assert section is not None

    assert section["id"] == "a/b/c"
    assert section["type"] == "resource"
    assert "children" not in section


def test_create_fs_genomic_resource_repository(fixture_dirname):
    repo = create_fs_genomic_resource_repository(
        "test_repo", fixture_dirname("genomic_resources"))
    assert repo is not None


def test_get_resources(root_group):
    print(list(root_group.get_genomic_resources()))
    assert len(list(root_group.get_genomic_resources())) == 1
    res = next(root_group.get_genomic_resources())
    assert res.get_id() == "a/b/c"

    g = root_group.get_resource("a")
    g.add_child(GenomicResourceGroup("a/aa"))

    assert len(list(root_group.get_genomic_resources())) == 1
    res = next(root_group.get_genomic_resources())
    assert res.get_id() == "a/b/c"


def test_resource_paths(fixture_dirname):
    repo = create_fs_genomic_resource_repository(
        "test_repo", fixture_dirname("genomic_resources"))
    assert repo is not None
    for resource in repo.root_group.get_genomic_resources():
        print(resource, resource.get_path())
        assert os.path.exists(resource.get_path())

        url = urlparse(resource.get_url()).path
        print(url)


def test_build_manifests(fixture_dirname):
    repo = create_fs_genomic_resource_repository(
        "test_repo", fixture_dirname("genomic_resources"))
    assert repo is not None
    for resource in repo.root_group.get_genomic_resources():
        repo.build_resource_manifest(resource.get_id())


def test_walk_genomic_resources_repository_content(fixture_dirname, fake_repo):
    repo_dirname = fixture_dirname("genomic_resources")
    print(repo_dirname)

    content_path = os.path.join(repo_dirname, "CONTENT.yaml")
    if os.path.exists(content_path):
        with open(content_path, "r") as content:
            repo_content = yaml.safe_load(content)

    print(repo_content)

    for parents, child, in _walk_genomic_repository_content(
            fake_repo, repo_content):
        print(parents, child)
