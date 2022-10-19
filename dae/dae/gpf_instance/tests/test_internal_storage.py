# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

from dae.testing import setup_gpf_instance, setup_genome, \
    setup_empty_gene_models, setup_directories


def test_internal_genotype_storage(tmp_path_factory):
    # Given
    root_path = tmp_path_factory.mktemp("internal_storage_test")

    genome = setup_genome(
        root_path / "alla_gpf" / "genome" / "allChr.fa",
        f"""
        >chrA
        {100 * "A"}
        """
    )
    empty_gene_models = setup_empty_gene_models(
        root_path / "alla_gpf" / "empty_gene_models" / "empty_genes.txt")
    gpf = setup_gpf_instance(
        root_path / "gpf_instance",
        reference_genome=genome,
        gene_models=empty_gene_models,
    )

    # When
    internal_storage = gpf.genotype_storages.get_genotype_storage("internal")

    # Then
    assert internal_storage.get_storage_type() == "inmemory"
    assert internal_storage.storage_config["dir"] == \
        str(root_path / "gpf_instance" / "internal_storage")
    assert gpf.genotype_storages.get_default_genotype_storage() == \
        internal_storage


def test_internal_genotype_storage_with_other_storages(tmp_path_factory):
    # Given
    root_path = tmp_path_factory.mktemp("internal_storage_test")

    genome = setup_genome(
        root_path / "alla_gpf" / "genome" / "allChr.fa",
        f"""
        >chrA
        {100 * "A"}
        """
    )
    empty_gene_models = setup_empty_gene_models(
        root_path / "alla_gpf" / "empty_gene_models" / "empty_genes.txt")

    setup_directories(root_path / "gpf_instance", {
        "gpf_instance.yaml": textwrap.dedent("""
        genotype_storage:
            default: alabala
            storages:
            - id: alabala
              storage_type: inmemory
              dir: "%(wd)s/alabala_storage"
        """)
    })

    gpf = setup_gpf_instance(
        root_path / "gpf_instance",
        reference_genome=genome,
        gene_models=empty_gene_models,
    )

    # When
    internal_storage = gpf.genotype_storages.get_genotype_storage("internal")

    # Then
    assert internal_storage.get_storage_type() == "inmemory"
    assert internal_storage.storage_config["dir"] == \
        str(root_path / "gpf_instance" / "internal_storage")
    assert gpf.genotype_storages.get_default_genotype_storage() != \
        internal_storage
