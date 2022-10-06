# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

from dae.testing import \
    setup_directories, setup_genome, setup_gene_models

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
    genome = setup_genome(
        root_path / "foobar_genome" / "chrAll.fa",
        """
            >foo
            NNACCCAAAC
            GGGCCTTCCN
            NNNA
            >bar
            NNGGGCCTTC
            CACGACCCAA
            NN
        """
    )
    genes = setup_gene_models(
        root_path / "foobar_genes" / "genes.txt",
        GMM_CONTENT, fileformat="refflat")
    content = {
        "gpf_instance": {
            "gpf_instance.yaml": "",
        }
    }
    setup_directories(root_path, content)
    gpf_instance = GPFInstance(
        work_dir=str(root_path / "gpf_instance"),
        reference_genome=genome,
        gene_models=genes)

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
