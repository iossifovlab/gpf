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
        .get_file_content("CADD.bedgraph.gz.tbi")
    file_content = dir_repo.get_resource("hg19/CADD")\
        .get_file_content("CADD.bedgraph.gz.tbi")
    assert s3_content == file_content
