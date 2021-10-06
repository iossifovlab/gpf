import pytest
import os

from dae.genomic_resources.resources import GenomicResource, \
    GenomicResourceGroup
from dae.genomic_resources.repository import \
    _walk_genomic_resources_repository, \
    _create_genomic_resources_hierarchy, \
    _create_resource_content_dict, \
    create_fs_genomic_resource_repository


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


# def test_resource_paths(fixture_dirname):
#     repo = create_fs_genomic_resource_repository(
#         "test_repo", fixture_dirname("genomic_resources"))
#     assert repo is not None
#     for resource in repo.root_group.get_genomic_resources():
#         print(resource, resource.get_path())
#         assert os.path.exists(resource.get_path())

#         url = urlparse(resource.get_url()).path
#         print(url)


def test_build_manifests(fixture_dirname):
    repo = create_fs_genomic_resource_repository(
        "test_repo", fixture_dirname("genomic_resources"))
    assert repo is not None
    for resource in repo.root_group.get_genomic_resources():
        repo.build_resource_manifest(resource.get_id())


def test_lazy_manifest_timestamp_check(fixture_dirname):
    repo = create_fs_genomic_resource_repository(
        "test_repo", fixture_dirname("genomic_resources"))
    assert repo is not None
    for resource in repo.root_group.get_genomic_resources():
        manifest_path = os.path.join(
            resource.get_url().replace("file://", ""), "MANIFEST"
        )
        mtime_old = os.path.getmtime(manifest_path)
        repo.build_resource_manifest(resource.get_id())
        mtime_new = os.path.getmtime(manifest_path)
        assert mtime_new == mtime_old


def test_lazy_manifest_outdated_timestamp(fixture_dirname):
    repo = create_fs_genomic_resource_repository(
        "test_repo", fixture_dirname("genomic_resources"))
    assert repo is not None
    for resource in repo.root_group.get_genomic_resources():
        manifest_path = os.path.join(
            resource.get_url().replace("file://", ""), "MANIFEST"
        )
        mtime_old = os.path.getmtime(manifest_path)
        # update timestamp of some resource file to force manifest rebuild
        os.utime(
            repo.get_file_urls(resource.get_id())[0].replace("file://", ""),
            (mtime_old + 1, mtime_old + 1)
        )
        repo.build_resource_manifest(resource.get_id())
        mtime_new = os.path.getmtime(manifest_path)
        assert mtime_new > mtime_old
