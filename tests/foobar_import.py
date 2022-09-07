# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

from dae.genomic_resources import build_genomic_resource_repository

from dae.genomic_resources.testing import convert_to_tab_separated, \
    setup_directories

from dae.gpf_instance import GPFInstance
from dae.import_tools.import_tools import ImportProject, run_with_project


# this content follows the 'refflat' gene model format
GMM_CONTENT = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
g1        tx1  foo   +      3       15    3        13     2         3,7        6,13
g1        tx2  foo   +      3       9     3        6      1         3          6
g2        tx3  bar   -      10      20    12       18     1         12         18
"""  # noqa


def foobar_gpf(root_path):
    content = {
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
                  default: genotype_impala
                  storages:
                  - id: genotype_impala
                    storage_type: impala
                    dir: "work/"
                    hdfs:
                      base_dir: /tmp/test_data1
                      host: localhost
                      port: 8020
                      replication: 1
                    impala:
                      db: "test_schema1"
                      hosts:
                      - localhost
                      pool_size: 3
                      port: 21050
                  - id: genotype_impala_2
                    storage_type: impala2
                    dir: "work/"
                    hdfs:
                      base_dir: /tmp/test_data2
                      host: localhost
                      port: 8020
                      replication: 1
                    impala:
                      db: "test_schema2"
                      hosts:
                      - localhost
                      pool_size: 3
                      port: 21050
                    schema_version: 2
                  - id: genotype_filesystem
                    storage_type: filesystem
                    dir: "{root_path}/genotype_filesystem"
            """)
        }
    }
    setup_directories(root_path, content)
    grr = build_genomic_resource_repository({
        "id": "minimal",
        "type": "file",
        "directory": str(root_path / "grr")
    })
    gpf_instance = GPFInstance(
        work_dir=str(root_path / "gpf_instance"),
        grr=grr)
    return gpf_instance


def foobar_vcf_import(root_path, study_id, ped_path, vcf_path, storage_id):

    foobar_gpf(root_path)

    config = textwrap.dedent(f"""
        id: {study_id}
        processing_config:
          work_dir: {root_path / "work"}
        input:
          pedigree:
            file: {ped_path}
          vcf:
            files:
             - {vcf_path}
            denovo_mode: denovo
            omission_mode: omission
        gpf_instance:
          path: {root_path / "gpf_instance"}
        destination:
          storage_id: {storage_id}
        """)
    setup_directories(root_path, {
        "vcf_project": {
            "vcf_project.yaml": config
        },
    })
    project = ImportProject.build_from_file(
        root_path / "vcf_project" / "vcf_project.yaml")
    run_with_project(project)
    return project
