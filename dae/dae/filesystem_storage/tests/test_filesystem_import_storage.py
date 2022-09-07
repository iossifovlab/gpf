# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import textwrap

import pytest

from dae.genomic_resources.testing import setup_directories, \
    convert_to_tab_separated
from dae.import_tools.import_tools import ImportProject
from dae.filesystem_storage.filesystem_import_storage import \
    FilesystemImportStorage


# this content follows the 'refflat' gene model format
GMM_CONTENT = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
g1        tx1  foo   +      3       15    3        13     2         3,7        6,13
g1        tx2  foo   +      3       9     3        6      1         3          6
g2        tx3  bar   -      10      20    12       18     1         12         18
"""  # noqa


@pytest.fixture
def simple_project(tmp_path):
    setup_directories(tmp_path, {
        "grr": {
            "foobar_genome": {
                "chrAll.fa": convert_to_tab_separated("""
                        >foo
                        NNACCCAAAC
                        GGGCCTTCCN
                        NNNA
                        >bar
                        NNGGGCCTTC
                        CACGACCCAA
                        NN
                """),
                "chrAll.fa.fai": convert_to_tab_separated("""
                    foo  24  5  10  11
                    bar  22  36 10  11
                """),
                "genomic_resource.yaml": textwrap.dedent("""
                    type: genome
                    filename: chrAll.fa
                """)
            },
            "foobar_genes": {
                "genes.txt": convert_to_tab_separated(GMM_CONTENT),
                "genomic_resource.yaml": textwrap.dedent("""
                    type: gene_models
                    filename: genes.txt
                    format: refflat
                """)
            },
        },
        "gpf_instance": {
            "gpf_instance.yaml": textwrap.dedent(f"""
                grr:
                    id: "minimal"
                    type: "file"
                    directory: {tmp_path / "grr"}
                reference_genome:
                    resource_id: "foobar_genome"
                gene_models:
                    resource_id: "foobar_genes"
                genotype_storage:
                  default: genotype_filesystem
                  storages:
                  - id: genotype_filesystem
                    storage_type: filesystem
                    dir: "{tmp_path}/filesystem_storage"
            """)
        },
        "project": {
            "project.yaml": textwrap.dedent(f"""
                id: test_import
                input:
                  pedigree:
                    file: pedigree.ped
                    family: fId
                    person: pId
                    mom: mId
                    dad: dId
                  denovo:
                    files:
                      - denovo.tsv
                    person_id: spid
                    family_id: fId
                    chrom: chrom
                    pos: pos
                    ref: ref
                    alt: alt
                    genotype: genotype
                gpf_instance:
                    path: {tmp_path / "gpf_instance"}
                destination:
                    storage_id: genotype_filesystem
            """),
            "pedigree.ped": convert_to_tab_separated("""
                fId pId      mId    dId    sex status      role
                f1  f1.dad   0      0      M   unaffected  dad
                f1  f1.mom   0      0      F   unaffected  mom
                f1  f1.s1    f1.mom f1.dad F   unaffected  sib
                f1  f1.p1    f1.mom f1.dad M   affected    prb
                f1  f1.s2    f1.mom f1.dad F   affected    sib
            """),
            "denovo.tsv": convert_to_tab_separated("""
                fId chrom pos ref alt genotype             spid
                f1  foo   11  G   C   0/0,0/0,0/1,0/0,0/1  f1.s1
                f1  bar   11  C   G   0/0,0/0,0/1,0/0,0/1  f1.s1
            """),
        }
    })
    project = ImportProject.build_from_file(
        tmp_path / "project" / "project.yaml")
    return project


def test_simple_project_storage_type(simple_project):
    assert simple_project._storage_type() == "filesystem"


def test_simple_project_pedigree_params(simple_project):
    fname, params = simple_project.get_pedigree_params()

    assert fname.endswith("pedigree.ped")
    assert params["ped_family"] == "fId"
    assert params["ped_person"] == "pId"
    assert params["ped_mom"] == "mId"
    assert params["ped_dad"] == "dId"


def test_simple_project_pedigree_size(simple_project):
    pedigree = simple_project.get_pedigree()
    assert len(pedigree) == 1
    assert len(pedigree.persons) == 5


def test_simple_project_destination_study_dir(simple_project):
    dest = FilesystemImportStorage._get_destination_study_dir(simple_project)
    assert dest.endswith("filesystem_storage/test_import")
    assert os.path.exists(dest)


def test_simple_project_get_loader_types(simple_project):
    loader_types = simple_project.get_import_variants_types()
    assert loader_types == {"denovo"}


def test_study_dir_pedigree(simple_project):
    dest = FilesystemImportStorage._do_copy_pedigree(simple_project)
    assert dest["path"].endswith("filesystem_storage/test_import/pedigree.ped")
    assert os.path.exists(dest["path"])


def test_study_dir_denovo_variants(simple_project):
    dest = FilesystemImportStorage._do_copy_variants(simple_project, "denovo")
    assert len(dest) == 1

    assert dest[0]["path"].endswith(
        "filesystem_storage/test_import/denovo.tsv")
    assert os.path.exists(dest[0]["path"][0])


def test_study_import(simple_project):
    FilesystemImportStorage._do_study_import(simple_project)
    gpf_instance = simple_project.get_gpf_instance()
    gpf_instance.reload()

    study = gpf_instance.get_genotype_data("test_import")
    fvs = list(study.query_variants())
    assert len(fvs) == 2
