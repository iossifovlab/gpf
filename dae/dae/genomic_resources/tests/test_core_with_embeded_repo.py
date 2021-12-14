from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo


def test_the_basic_resource_finding():
    repo = GenomicResourceEmbededRepo("oneResource", {
        "one": {"genomic_resource.yaml": ""}
    })
    gr = repo.get_resource("one")
    assert gr
    assert gr.resource_id == "one"
    assert gr.version == (0,)
    assert gr.repo.repo_id == "oneResource"


def test_not_finding_resource_with_the_required_version():
    repo = GenomicResourceEmbededRepo("oneResource", {
        "one": {"genomic_resource.yaml": ""}
    })

    gr = repo.get_resource("one", version_constraint="1.0")
    assert not gr


def test_finding_resource_with_version_and_repo_id():
    repo = GenomicResourceEmbededRepo("oneResource", content={
        "one[1.0]": {"genomic_resource.yaml": ""}
    })
    gr = repo.get_resource("one", version_constraint="1.0",
                           genomic_repository_id="oneResource")
    assert gr
    assert gr.resource_id == "one"
    assert gr.version == (1, 0)
    assert gr.repo.repo_id == "oneResource"


def test_md5_checksum():
    repo = GenomicResourceEmbededRepo("a", {"one": {
        "genomic_resource.yaml": "type: genome\nseqFile: chrAll.fa",
        "chrAll.fa": ">chr1\nAACCCCACACACACACACACCAC\n",
        "chrAll.fa.fai": "chr1\t30\t50\n",
    }})

    gr = repo.get_resource("one")
    assert gr.get_md5_sum("chrAll.fa") == "a778802ca2a9c24a08981f9be4f2f31f"


def test_manifest_file_creation():
    repo = GenomicResourceEmbededRepo("a", {
        "one": {
            "genomic_resource.yaml": ["", '2000-03-03'],
            "data.txt": ["some data", '2000-03-08T10:03:03'],
            "stats": {
                "hists.txt": ["1,3,4", '1999-03-08T10:03:03'],
                "hists.png": ["PNG", '1999-03-08T10:04:03']
            }
        }
    })
    gr = repo.get_resource("one")
    assert gr.get_manifest() == [
        {'name': 'data.txt', 'size': 9, 'time': '2000-03-08T10:03:03',
         'md5': '1e50210a0202497fb79bc38b6ade6c34'},
        {'name': 'genomic_resource.yaml', 'size': 0, 'time': '2000-03-03',
         'md5': 'd41d8cd98f00b204e9800998ecf8427e'},
        {'name': 'stats/hists.png', 'size': 3, 'time': '1999-03-08T10:04:03',
         'md5': '55505ba281b015ec31f03ccb151b2a34'},
        {'name': 'stats/hists.txt', 'size': 5, 'time': '1999-03-08T10:03:03',
         'md5': '9d9676541599e2054d98df2d361775c0'}]


def test_type_of_genomic_resoruces():
    from dae.genomic_resources import ReferenceGenomeResource
    repo = GenomicResourceEmbededRepo("a", {"one": {
        "genomic_resource.yaml": "type: genome\nseqFile: chrAll.fa",
        "chrAll.fa": ">chr1\nAACCCCACACACACACACACCAC",
        "chrAll.fa.fai": "chr1\t30\t50",
    }})
    gr = repo.get_resource("one")
    assert gr
    assert isinstance(gr, ReferenceGenomeResource)


def test_resources_files():
    repo = GenomicResourceEmbededRepo("a", {
        "one": {
            "genomic_resource.yaml": ["", '2000-03-03'],
            "data.txt": ["some data", '2000-03-08T10:03:03'],
            "stats": {
                "hists.txt": ["1,3,4", '1999-03-08T10:04:03'],
                "hists.png": ["PNG", '1999-03-08T10:03:03']
            }
        }
    })
    gr = repo.get_resource("one")
    assert gr

    assert {(fn, fs, ft) for fn, fs, ft in gr.get_files()} == {
        ("genomic_resource.yaml", 0, '2000-03-03'),
        ("data.txt", 9, '2000-03-08T10:03:03'),
        ("stats/hists.txt", 5, '1999-03-08T10:04:03'),
        ("stats/hists.png", 3, '1999-03-08T10:03:03')}
