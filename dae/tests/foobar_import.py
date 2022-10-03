# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
import pathlib

import pysam

from dae.genomic_resources.testing import convert_to_tab_separated, \
    setup_directories
from dae.import_tools.import_tools import ImportProject, run_with_project
from dae.gpf_instance import GPFInstance


# this content follows the 'refflat' gene model format
GMM_CONTENT = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
g1        tx1  foo   +      3       15    3        13     2         3,7        6,13
g1        tx2  foo   +      3       9     3        6      1         3          6
g2        tx3  bar   -      10      20    12       18     1         12         18
"""  # noqa


def foobar_gpf(root_path, storage=None):
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
            """)
        }
    }
    setup_directories(root_path, content)
    gpf_instance = GPFInstance(work_dir=str(root_path / "gpf_instance"))
    if storage:
        gpf_instance\
            .genotype_storage_db\
            .register_genotype_storage(storage)
    return gpf_instance


def foobar_vcf_import(root_path, study_id, ped_path, vcf_path, storage):

    gpf_instance = foobar_gpf(root_path)
    gpf_instance.genotype_storage_db.register_genotype_storage(storage)

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
        destination:
          storage_id: {storage.storage_id}
        """)
    setup_directories(root_path, {
        "vcf_project": {
            "vcf_project.yaml": config
        },
    })
    project = ImportProject.build_from_file(
        root_path / "vcf_project" / "vcf_project.yaml",
        gpf_instance=gpf_instance)
    run_with_project(project)
    return project


def foobar_vcf_study(root_path, study_id, ped_path, vcf_path, storage):
    import_project = foobar_vcf_import(
        root_path, study_id, ped_path, vcf_path, storage)
    gpf_instance = import_project.get_gpf_instance()
    gpf_instance.reload()

    study = gpf_instance.get_genotype_data(study_id)
    return study


def setup_pedigree(ped_path, content):
    ped_data = convert_to_tab_separated(content)
    setup_directories(ped_path, ped_data)
    return str(ped_path)


def setup_denovo(denovo_path, content):
    denovo_data = convert_to_tab_separated(content)
    setup_directories(denovo_path, denovo_data)
    return str(denovo_path)


def setup_vcf(out_path: pathlib.Path, content):
    vcf_data = convert_to_tab_separated(content)
    vcf_path = out_path
    if out_path.suffix == "gz":
        vcf_path = out_path.with_suffix("")

    setup_directories(vcf_path, vcf_data)

    if out_path.suffix == "gz":
        vcf_gz_filename = str(vcf_path.parent / f"{vcf_path.name}.gz")
        # pylint: disable=no-member
        pysam.tabix_compress(str(vcf_path), vcf_gz_filename)
        pysam.tabix_index(vcf_gz_filename, preset="vcf")

    return str(out_path)


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
