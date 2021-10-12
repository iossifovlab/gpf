import os
import yaml

from dae.genomic_resources.repository import \
    _walk_genomic_repository_content, \
    _walk_genomic_resources_repository


def test_repository_content_walker(fake_repo):
    content = {
        "id": "",
        "type": "group",
        "children": [
            {
                "id": "hg19",
                "type": "group",
                "children": [
                    {
                        "id": "hg19/MPC",
                        "type": "resource"
                    }
                ]
            }
        ]
    }

    walker = _walk_genomic_repository_content(fake_repo, content)

    parents, child = next(walker)
    assert parents == ("hg19", )
    assert child == ("MPC", "/repo/path/hg19/MPC/genomic_resource.yaml")


# def test_genomic_resource_repository_walker(fixture_dirname):
#     repo_dirname = fixture_dirname("genomic_resources")
#     walker = _walk_genomic_resources_repository(repo_dirname)

#     parents, child = next(walker)
#     print(parents, child)

#     assert parents == ("hg19", "internal")
#     child_id, child_path = child
#     assert child_id == "scores_incomplete_coverage"
#     assert child_path.endswith(
#         "genomic_resources/hg19/internal/scores_incomplete_coverage/"
#         "genomic_resource.yaml")


def test_walk_genomic_resources_repository(fixture_dirname):
    repo_dirname = fixture_dirname("genomic_resources")
    print(repo_dirname)

    for parents, child, in _walk_genomic_resources_repository(repo_dirname):
        print(parents, child)

    all_resources = list(_walk_genomic_resources_repository(repo_dirname))
    assert len(all_resources) == 14

    all_resources_ids = set([
        (*parents, child[0]) for parents, child in all_resources
    ])
    print(all_resources_ids)

    assert (
        'hg19',
        'GATK_ResourceBundle_5777_b37_phiX174',
        'genome') in all_resources_ids

    assert ("hg19", "CADD") in all_resources_ids


def test_walk_genomic_resources_repository_content(fixture_dirname, fake_repo):
    repo_dirname = fixture_dirname("genomic_resources")
    print(repo_dirname)

    content_path = os.path.join(repo_dirname, "CONTENT.yaml")
    assert os.path.exists(content_path)
    with open(content_path, "r") as content:
        repo_content = yaml.safe_load(content)

    for parents, child, in _walk_genomic_repository_content(
            fake_repo, repo_content):
        print(parents, child)

    all_resources = list(_walk_genomic_repository_content(
            fake_repo, repo_content))
    assert len(all_resources) == 14

    all_resources_ids = set([
        (*parents, child[0]) for parents, child in all_resources
    ])
    print(all_resources_ids)

    assert (
        'hg19',
        'GATK_ResourceBundle_5777_b37_phiX174',
        'genome') in all_resources_ids

    assert ("hg19", "CADD") in all_resources_ids
