# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

import pytest
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.genomic_resources.testing import (
    setup_directories,
    setup_empty_gene_models,
    setup_genome,
    setup_pedigree,
    setup_vcf,
)
from dae.testing.import_helpers import vcf_study
from dae.testing.setup_helpers import setup_gpf_instance


def test_internal_genotype_storage(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    # Given
    root_path = tmp_path_factory.mktemp("internal_storage_test")

    setup_genome(
        root_path / "alla_gpf" / "genome" / "allChr.fa",
        f"""
        >chrA
        {100 * "A"}
        """,
    )
    setup_empty_gene_models(
        root_path / "alla_gpf" / "empty_gene_models" / "empty_genes.txt")
    local_repo = build_genomic_resource_repository({
        "id": "alla_local",
        "type": "directory",
        "directory": str(root_path / "alla_gpf"),
    })
    gpf = setup_gpf_instance(
        root_path / "gpf_instance",
        reference_genome_id="genome",
        gene_models_id="empty_gene_models",
        grr=local_repo,
    )

    # When
    internal_storage = gpf.genotype_storages.get_genotype_storage("internal")

    # Then
    assert internal_storage.storage_type == "duckdb_parquet"
    assert internal_storage.storage_config["base_dir"] == \
        root_path / "gpf_instance" / "internal_storage"
    assert gpf.genotype_storages.get_default_genotype_storage() == \
        internal_storage


def test_internal_genotype_storage_with_other_storages(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    # Given
    root_path = tmp_path_factory.mktemp("internal_storage_test")

    setup_genome(
        root_path / "alla_gpf" / "genome" / "allChr.fa",
        f"""
        >chrA
        {100 * "A"}
        """,
    )
    setup_empty_gene_models(
        root_path / "alla_gpf" / "empty_gene_models" / "empty_genes.txt")

    setup_directories(root_path / "gpf_instance", {
        "gpf_instance.yaml": textwrap.dedent("""
        instance_id: test_instance
        genotype_storage:
            default: alabala
            storages:
            - id: alabala
              storage_type: inmemory
              dir: "%(wd)s/alabala_storage"
        """),
    })
    local_repo = build_genomic_resource_repository({
        "id": "alla_local",
        "type": "directory",
        "directory": str(root_path / "alla_gpf"),
    })

    gpf = setup_gpf_instance(
        root_path / "gpf_instance",
        reference_genome_id="genome",
        gene_models_id="empty_gene_models",
        grr=local_repo,
    )

    # When
    internal_storage = gpf.genotype_storages.get_genotype_storage("internal")

    # Then
    assert internal_storage.storage_type == "duckdb_parquet"
    assert internal_storage.storage_config["base_dir"] == \
        root_path / "gpf_instance" / "internal_storage"
    assert gpf.genotype_storages.get_default_genotype_storage() != \
        internal_storage


def test_internal_genotype_storage_import_study(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    # Given
    root_path = tmp_path_factory.mktemp("internal_storage_test")

    setup_genome(
        root_path / "alla_gpf" / "genome" / "allChr.fa",
        f"""
        >chrA
        {100 * "A"}
        """,
    )
    setup_empty_gene_models(
        root_path / "alla_gpf" / "empty_gene_models" / "empty_genes.txt")
    local_repo = build_genomic_resource_repository({
        "id": "alla_local",
        "type": "directory",
        "directory": str(root_path / "alla_gpf"),
    })
    gpf = setup_gpf_instance(
        root_path / "gpf_instance",
        reference_genome_id="genome",
        gene_models_id="empty_gene_models",
        grr=local_repo,
    )

    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     2   2      prb
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=foo>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  p1
        foo    13  .  G   C   .    .      .    GT     0/1 0/0 0/1
        foo    14  .  C   T   .    .      .    GT     0/0 0/1 0/1
        """)

    vcf_study(
        root_path,
        "minimal_vcf",
        ped_path,
        [vcf_path],
        gpf_instance=gpf,
    )

    # When
    internal_storage = gpf.genotype_storages.get_genotype_storage("internal")
    assert gpf.genotype_storages.get_default_genotype_storage() == \
        internal_storage

    data = gpf.get_all_genotype_data()
    assert len(data) == 1
    assert data[0].study_id == "minimal_vcf"
