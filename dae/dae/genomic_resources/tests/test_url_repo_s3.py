def test_s3_url_vs_dir_results(genomic_resource_fixture_dir_repo,
                               genomic_resource_fixture_s3_repo):
    dir_repo = genomic_resource_fixture_dir_repo
    s3_repo = genomic_resource_fixture_s3_repo

    def resource_set(repo):
        return {
            (gr.resource_id, gr.version) for gr in repo.get_all_resources()
        }

    assert len(list(s3_repo.get_all_resources())) == \
        len(list(s3_repo.get_all_resources()))
    assert resource_set(dir_repo) == resource_set(s3_repo)

    # pick one file at random and assert content is the same
    s3_content = s3_repo.get_resource("hg19/CADD")\
        .get_file_content("CADD.bedgraph.gz.tbi", mode="b")
    file_content = dir_repo.get_resource("hg19/CADD")\
        .get_file_content("CADD.bedgraph.gz.tbi", mode="b")
    assert s3_content == file_content


def test_writing_to_s3_repo(genomic_resource_fixture_s3_repo):
    resource = genomic_resource_fixture_s3_repo.get_resource("hg19/CADD")
    with resource.open_raw_file("test-file", "wt") as file:
        file.write("Test")
    s3_filesystem = genomic_resource_fixture_s3_repo.filesystem
    assert s3_filesystem.exists("test-bucket/hg19/CADD/test-file")


def test_url_repository_file_exists(genomic_resource_fixture_s3_repo):
    repo = genomic_resource_fixture_s3_repo
    res = repo.get_resource("hg19/CADD")

    assert repo.file_exists(res, "CADD.bedgraph.gz.tbi")
    assert not repo.file_exists(res, "missing_file")
    assert res.file_exists("CADD.bedgraph.gz.tbi")
