# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

import pytest

from dae.testing import setup_directories, \
    convert_to_tab_separated
from dae.import_tools.import_tools import ImportProject

# this content follows the 'refflat' gene model format
GMM_CONTENT = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
g1        tx1  foo   +      3       15    3        13     2         3,7        6,13
g1        tx2  foo   +      3       9     3        6      1         3          6
g2        tx3  bar   -      10      20    12       18     1         12         18
"""  # noqa


@pytest.fixture(scope="module")
def simple_project(tmp_path_factory):
    root_path = tmp_path_factory.mktemp("root_path") / "simple_project"
    setup_directories(root_path, {
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
                    directory: {root_path / "grr"}
                reference_genome:
                    resource_id: "foobar_genome"
                gene_models:
                    resource_id: "foobar_genes"
                genotype_storage:
                  default: genotype_filesystem
                  storages:
                  - id: genotype_filesystem
                    storage_type: filesystem
                    dir: "{root_path}/storage"
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
                    path: {root_path / "gpf_instance"}
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
        root_path / "project" / "project.yaml")
    return project
