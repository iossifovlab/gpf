# pylint: disable=redefined-outer-name,C0114,C0116,protected-access

import pytest

from dae.genomic_resources.testing import build_testing_repository
from dae.genomic_resources.repository import GenomicResource, Manifest


def test_the_basic_resource_finding(tmp_path):
    repo = build_testing_repository(
        repo_id="oneResource", 
        root_path=str(tmp_path),
        content={
            "one": {"genomic_resource.yaml": ""}
        })
    res = repo.get_resource("one")
    assert res
    assert res.resource_id == "one"
    assert res.version == (0,)
    assert res.protocol.proto_id == "oneResource"


def test_not_finding_resource_with_the_required_version(tmp_path):
    repo = build_testing_repository(
        repo_id="oneResource", 
        root_path=str(tmp_path),
        content={
            "one": {"genomic_resource.yaml": ""}
        })

    with pytest.raises(FileNotFoundError):
        repo.get_resource("one", version_constraint="1.0")


def test_finding_resource_with_version_and_repo_id(tmp_path):
    repo = build_testing_repository(
        repo_id="oneResource",
        root_path=str(tmp_path),
        content={
            "one(1.0)": {"genomic_resource.yaml": ""}
        })
    res = repo.get_resource(
        "one", version_constraint="=1.0",
        repository_id="oneResource")
    assert res
    assert res.resource_id == "one"
    assert res.version == (1, 0)
    assert res.protocol.proto_id == "oneResource"


def test_md5_checksum(tmp_path):
    repo = build_testing_repository(
        repo_id="a",
        root_path=str(tmp_path),
        content={
            "one": {
                "genomic_resource.yaml": "type: genome\nseqFile: chrAll.fa",
                "chrAll.fa": ">chr1\nAACCCCACACACACACACACCAC\n",
                "chrAll.fa.fai": "chr1\t30\t50\n",
            }
        })

    res = repo.get_resource("one")
    assert repo.protocol.compute_md5_sum(res, "chrAll.fa") == \
        "a778802ca2a9c24a08981f9be4f2f31f"


def test_manifest_file_creation(tmp_path):
    repo = build_testing_repository(
        repo_id="a", 
        root_path=str(tmp_path),
        content={
            "one": {
                "genomic_resource.yaml": "",
                "data.txt": "some data",
                "stats": {
                    "hists.txt": "1,3,4",
                    "hists.png": "PNG",
                }
            }
        })
    res = repo.get_resource("one")
    assert res.get_manifest() == Manifest.from_manifest_entries([
        {"name": "data.txt", "size": 9, "time": "2000-03-08T10:03:03",
         "md5": "1e50210a0202497fb79bc38b6ade6c34"},
        {"name": "genomic_resource.yaml", "size": 0, "time": "2000-03-03",
         "md5": "d41d8cd98f00b204e9800998ecf8427e"},
        {"name": "stats/hists.png", "size": 3, "time": "1999-03-08T10:04:03",
         "md5": "55505ba281b015ec31f03ccb151b2a34"},
        {"name": "stats/hists.txt", "size": 5, "time": "1999-03-08T10:03:03",
         "md5": "9d9676541599e2054d98df2d361775c0"}])


def test_type_of_genomic_resoruces(tmp_path):
    repo = build_testing_repository(
        root_id="a",
        root_path=str(tmp_path),
        content={"one": {
            "genomic_resource.yaml": "type: genome\nseqFile: chrAll.fa",
            "chrAll.fa": ">chr1\nAACCCCACACACACACACACCAC",
            "chrAll.fa.fai": "chr1\t30\t50",
        }})
    res = repo.get_resource("one")
    assert res
    assert isinstance(res, GenomicResource)
    assert res.get_type() == "genome"


def test_resources_files(tmp_path):
    repo = build_testing_repository(
        repo_id="a",
        root_path=str(tmp_path),
        content={
            "one": {
                "genomic_resource.yaml": "",
                "data.txt": "some data",
                "stats": {
                    "hists.txt": "1,3,4",
                    "hists.png": "PNG",
                }
            }
        })
    res = repo.get_resource("one")
    assert res

    assert {(fn, fs) for fn, fs, ft in res.get_manifest().get_files()} == {
        ("genomic_resource.yaml", 0),
        ("data.txt", 9),
        ("stats/hists.txt", 5,),
        ("stats/hists.png", 3,)}
