# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
import pysam

from dae.genomic_resources.testing import convert_to_tab_separated, \
    setup_directories
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


def setup_vcf(root_path, content, name="in.vcf"):
    in_vcf = convert_to_tab_separated(content)

    setup_directories(root_path, {
        "vcf_data": {
            name: in_vcf,
        }
    })

    # pylint: disable=no-member
    pysam.tabix_compress(
        str(root_path / "vcf_data" / name),
        str(root_path / "vcf_data" / f"{name}.gz"))
    pysam.tabix_index(
        str(root_path / "vcf_data" / f"{name}.gz"), preset="vcf")

    return str(root_path / "vcf_data" / f"{name}.gz")


def setup_dae_transmitted(root_path, summary_content, toomany_content):
    summary = convert_to_tab_separated(summary_content)
    toomany = convert_to_tab_separated(toomany_content)

    setup_directories(root_path, {
        "dae_transmitted_data": {
            "tr.txt": summary,
            "tr-TOOMANY.txt": toomany
        }
    })

    # pylint: disable=no-member
    pysam.tabix_compress(
        str(root_path / "dae_transmitted_data" / "tr.txt"),
        str(root_path / "dae_transmitted_data" / "tr.txt.gz"))
    pysam.tabix_compress(
        str(root_path / "dae_transmitted_data" / "tr-TOOMANY.txt"),
        str(root_path / "dae_transmitted_data" / "tr-TOOMANY.txt.gz"))

    pysam.tabix_index(
        str(root_path / "dae_transmitted_data" / "tr.txt.gz"),
        seq_col=0, start_col=1, end_col=1, line_skip=1)
    pysam.tabix_index(
        str(root_path / "dae_transmitted_data" / "tr-TOOMANY.txt.gz"),
        seq_col=0, start_col=1, end_col=1, line_skip=1)

    return (str(root_path / "dae_transmitted_data" / "tr.txt.gz"),
            str(root_path / "dae_transmitted_data" / "tr-TOOMANY.txt.gz"))
