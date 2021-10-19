from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo
from dae.genomic_resources.group_repository import GenomicResourceGroupRepo


def test_lookup_priority_in_a_group_repository():
    repo = GenomicResourceGroupRepo(children=[
        GenomicResourceEmbededRepo("a", content={
            "one": {"genomic_resource.yaml": ""}}),
        GenomicResourceEmbededRepo("b", content={
            "one[1.0]": {"genomic_resource.yaml": ""}})
    ])
    gr = repo.get_resource("one")
    assert gr
    assert gr.resource_id == "one"
    assert gr.version == (0,)
    assert gr.repo.repo_id == "a"


def test_lookup_in_a_group_repository_with_version_requirement():
    repo = GenomicResourceGroupRepo([
        GenomicResourceEmbededRepo(
            "a", {"one": {"genomic_resource.yaml": ""}}),
        GenomicResourceEmbededRepo(
            "b", {"one[1.0]": {"genomic_resource.yaml": ""}})
    ])
    gr = repo.get_resource("one", version_constraint="1.0")
    assert gr
    assert gr.resource_id == "one"
    assert gr.version == (1, 0)
    assert gr.repo.repo_id == "b"
