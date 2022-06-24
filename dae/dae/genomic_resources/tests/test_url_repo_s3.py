# pylint: disable=W0621,C0114,C0116,W0212,W0613

def test_s3_url_vs_dir_results(fsspec_repo):

    dir_repo = fsspec_repo(scheme="file")
    s3_repo = fsspec_repo(scheme="s3")

    def resource_set(repo):
        return {
            (gr.resource_id, gr.version) for gr in repo.get_all_resources()
        }

    assert len(list(s3_repo.get_all_resources())) == \
        len(list(s3_repo.get_all_resources()))
    assert resource_set(dir_repo) == resource_set(s3_repo)

    # pick one file at random and assert content is the same
    s3_content = s3_repo.get_resource("one")\
        .get_file_content("test.txt.gz.tbi", mode="b")
    file_content = dir_repo.get_resource("one")\
        .get_file_content("test.txt.gz.tbi", mode="b")
    assert s3_content == file_content


def test_writing_to_s3_repo(fsspec_repo):
    s3_repo = fsspec_repo(scheme="s3")
    resource = s3_repo.get_resource("one")
    with resource.open_raw_file("test-file", "wt") as outfile:
        outfile.write("Test")
    fileurl = s3_repo.proto.get_resource_file_url(resource, "test-file")
    assert fileurl.endswith("one/test-file")

    s3_filesystem = s3_repo.proto.filesystem
    assert s3_filesystem.exists(fileurl)


def test_url_repository_file_exists(fsspec_repo):
    repo = fsspec_repo(scheme="s3")
    res = repo.get_resource("one")

    assert repo.proto.file_exists(res, "test.txt.gz.tbi")
    assert not repo.proto.file_exists(res, "missing_file")
    assert res.file_exists("test.txt.gz.tbi")
