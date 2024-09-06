# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

import pytest

from dae.genomic_resources.repository import (
    GR_CONF_FILE_NAME,
    GenomicResourceRepo,
)
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.testing import (
    setup_directories,
    setup_gpf_instance,
    setup_pedigree,
    setup_vcf,
    vcf_study,
)
from dae.testing.t4c8_import import t4c8_genes, t4c8_genome
from studies.study_wrapper import (
    StudyWrapper,
    StudyWrapperBase,
)


@pytest.fixture(scope="session")
def local_dir() -> pathlib.Path:
    return pathlib.Path(__file__).parents[4].joinpath("data/data-hg19-local")


@pytest.fixture(scope="session")
def local_gpf_instance(local_dir: pathlib.Path) -> GPFInstance:
    return GPFInstance.build(local_dir / "gpf_instance.yaml")


@pytest.fixture(scope="session")
def iossifov_2014_local(
        local_gpf_instance: GPFInstance) -> StudyWrapperBase:

    data_study = local_gpf_instance.get_genotype_data("iossifov_2014")

    return StudyWrapper(
        data_study,
        local_gpf_instance._pheno_registry,  # noqa: SLF001
        local_gpf_instance.gene_scores_db,
        local_gpf_instance,
    )


@pytest.fixture(scope="module")
def t4c8_grr(
    tmp_path_factory: pytest.TempPathFactory,
) -> GenomicResourceRepo:
    repo_path = tmp_path_factory.mktemp("t4c8_grr")
    t4c8_genome(repo_path)
    t4c8_genes(repo_path)

    setup_directories(
        repo_path / "gene_scores" / "t4c8_score",
        {
            GR_CONF_FILE_NAME:
            """
                type: gene_score
                filename: t4c8_gene_score.csv
                scores:
                - id: t4c8_score
                  desc: t4c8 gene score
                  histogram:
                    type: number
                    number_of_bins: 3
                    x_log_scale: false
                    y_log_scale: false
                """,
            "t4c8_gene_score.csv": textwrap.dedent("""
                gene,t4c8_score
                t4,10.123456789
                c8,20.0
            """),
        },
    )
    return build_genomic_resource_repository({
        "id": "t4c8_local",
        "type": "directory",
        "directory": str(repo_path),
    })


@pytest.fixture(scope="module")
def t4c8_instance(
    tmp_path_factory: pytest.TempPathFactory,
    t4c8_grr: GenomicResourceRepo,
) -> GPFInstance:
    root_path = tmp_path_factory.mktemp("t4c8_wgpf_instance")
    setup_directories(
        root_path / "gpf_instance", {
            "gpf_instance.yaml": textwrap.dedent("""
                instance_id: test_instance
                gene_scores_db:
                    gene_scores:
                    - "gene_scores/t4c8_score"
            """),
        },
    )
    gpf_instance = setup_gpf_instance(
        root_path / "gpf_instance",
        reference_genome_id="t4c8_genome",
        gene_models_id="t4c8_genes",
        grr=t4c8_grr,
    )

    storage_path = root_path / "duckdb_storage"
    storage_config = {
        "id": "duckdb_wgpf_test",
        "storage_type": "duckdb_parquet",
        "base_dir": str(storage_path),
    }
    gpf_instance.genotype_storages.register_storage_config(storage_config)
    _t4c8_study_2(gpf_instance)

    gpf_instance.reload()

    return gpf_instance


def _t4c8_study_2(
    t4c8_instance: GPFInstance,
) -> None:
    root_path = pathlib.Path(t4c8_instance.dae_dir)
    ped_path = setup_pedigree(
        root_path / "t4c8_study_2" / "pedigree" / "in.ped",
        """
familyId personId dadId momId sex status role
f1.1     mom1     0     0     2   1      mom
f1.1     dad1     0     0     1   1      dad
f1.1     p1       dad1  mom1  2   2      prb
f1.1     s1       dad1  mom1  1   1      sib
f1.3     mom3     0     0     2   1      mom
f1.3     dad3     0     0     1   1      dad
f1.3     p3       dad3  mom3  2   2      prb
f1.3     s3       dad3  mom3  2   1      sib
        """)
    vcf_path1 = setup_vcf(
        root_path / "t4c8_study_2" / "vcf" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
##contig=<ID=chr3>
#CHROM POS ID REF ALT  QUAL FILTER INFO FORMAT mom1 dad1 p1  s1  mom3 dad3 p3  s3
chr1   4   .  T   G,TA .    .      .    GT     0/1  0/1  0/0 0/0 0/1  0/2  0/2 0/0
chr1   54  .  T   C    .    .      .    GT     0/1  0/1  0/1 0/1 0/0  0/0  0/1 0/1
chr1   90  .  G   C,GA .    .      .    GT     0/1  0/2  0/2 0/2 0/1  0/2  0/1 0/2
chr1   100 .  T   G,TA .    .      .    GT     0/1  0/1  0/0 0/0 0/2  0/0  0/0 0/0
chr1   119 .  A   G,C  .    .      .    GT     0/0  0/0  0/2 0/2 0/1  0/2  0/1 0/2
chr1   122 .  A   C,AC .    .      .    GT     0/1  0/1  0/1 0/1 0/2  0/2  0/2 0/1
        """)  # noqa: E501

    vcf_study(
        root_path,
        "t4c8_study_2", ped_path, [vcf_path1],
        t4c8_instance,
        project_config_update={
            "input": {
                "vcf": {
                    "denovo_mode": "denovo",
                    "omission_mode": "omission",
                },
            },
        },
        study_config_update={
            "conf_dir": str(root_path / "t4c8_study_2"),
            "person_set_collections": {
                "phenotype": {
                    "id": "phenotype",
                    "name": "Phenotype",
                    "sources": [
                        {
                            "from": "pedigree",
                            "source": "status",
                        },
                    ],
                    "default": {
                        "color": "#aaaaaa",
                        "id": "unspecified",
                        "name": "unspecified",
                    },
                    "domain": [
                        {
                            "color": "#bbbbbb",
                            "id": "autism",
                            "name": "autism",
                            "values": [
                                "affected",
                            ],
                        },
                        {
                            "color": "#00ff00",
                            "id": "unaffected",
                            "name": "unaffected",
                            "values": [
                                "unaffected",
                            ],
                        },
                    ],
                },
                "selected_person_set_collections": [
                    "phenotype",
                ],
            },
        },
    )


@pytest.fixture(scope="module")
def t4c8_study_2(
    t4c8_instance: GPFInstance,
) -> StudyWrapperBase:

    data_study = t4c8_instance.get_genotype_data("t4c8_study_2")

    return StudyWrapper(
        data_study,
        t4c8_instance._pheno_registry,  # noqa: SLF001
        t4c8_instance.gene_scores_db,
        t4c8_instance,
    )
