# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest
import yaml
from dae.genomic_resources.testing import (
    setup_directories,
    setup_pedigree,
    setup_vcf,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.import_tools.cli import run_with_project
from dae.import_tools.import_tools import ImportProject
from dae.testing.import_helpers import vcf_study
from dae.utils.regions import Region
from dae.variants_loaders.parquet.loader import ParquetLoader


@pytest.fixture(scope="session")
def t4c8_parquet_study(t4c8_instance: GPFInstance) -> str:
    root_path = pathlib.Path(t4c8_instance.dae_dir)
    ped_path = setup_pedigree(
        root_path / "study" / "pedigree" / "in.ped",
        """
familyId personId dadId momId sex status role
f1.1     mom1     0     0     2   1      mom
f1.1     dad1     0     0     1   1      dad
f1.1     ch1      dad1  mom1  2   2      prb
f1.3     mom3     0     0     2   1      mom
f1.3     dad3     0     0     1   1      dad
f1.3     ch3      dad3  mom3  2   2      prb
        """)
    vcf_path1 = setup_vcf(
        root_path / "study" / "vcf" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
##contig=<ID=chr3>
#CHROM POS  ID REF ALT  QUAL FILTER INFO FORMAT mom1 dad1 ch1 mom3 dad3 ch3
chr1   4    .  T   G,TA .    .      .    GT     0/1  0/1  0/0 0/1  0/2  0/2
chr1   54   .  T   C    .    .      .    GT     0/1  0/1  0/1 0/1  0/0  0/1
chr1   90   .  G   C,GA .    .      .    GT     0/1  0/2  0/2 0/1  0/2  0/1
chr1   100  .  T   G,TA .    .      .    GT     0/1  0/1  0/0 0/2  0/2  0/0
chr1   119  .  A   G,C  .    .      .    GT     0/0  0/2  0/2 0/1  0/2  0/1
chr1   122  .  A   C,AC .    .      .    GT     0/1  0/1  0/1 0/2  0/2  0/2
        """)

    project_config_update = {
        "partition_description": {
            "region_bin": {
                "chromosomes": ["chr1"],
                "region_length": 100,
            },
            "frequency_bin": {
                "rare_boundary": 25.0,
            },
            "coding_bin": {
                "coding_effect_types": [
                    "frame-shift",
                    "noStart",
                    "missense",
                    "synonymous",
                ],
            },
            "family_bin": {
                "family_bin_size": 2,
            },
        },
    }
    vcf_study(
        root_path,
        "study", ped_path, [vcf_path1],
        t4c8_instance,
        project_config_update=project_config_update,
        project_config_overwrite={"destination": {"storage_type": "schema2"}},
    )
    return f"{root_path}/work_dir/study"


@pytest.fixture(scope="session")
def parquet_loader(
    t4c8_instance: GPFInstance,
    t4c8_parquet_study: str,
) -> ParquetLoader:
    return ParquetLoader(
        t4c8_parquet_study,
        genome=t4c8_instance.reference_genome,
        regions=None,
    )


@pytest.mark.parametrize(
    "region, expected", [
        (None, 6),
        (Region("chr1", 54, 100), 3),
    ],
)
def test_fetch_variants(
    parquet_loader: ParquetLoader,
    region: Region | None,
    expected: int,
) -> None:
    variants = list(parquet_loader.fetch(region=region))
    assert len(variants) == expected


@pytest.mark.parametrize(
    "region, expected", [
        (None, 6),
        (Region("chr1", 54, 100), 3),
    ],
)
def test_fetch_summary_variants(
    parquet_loader: ParquetLoader,
    region: Region | None,
    expected: int,
) -> None:
    variants = list(parquet_loader.fetch_summary_variants(region=region))
    assert len(variants) == expected


@pytest.mark.parametrize(
    "region, expected", [
        (None, 12),
        (Region("chr1", 54, 100), 6),
    ],
)
def test_fetch_family_variants(
    parquet_loader: ParquetLoader,
    region: Region | None,
    expected: int,
) -> None:
    variants = list(parquet_loader.fetch_family_variants(region=region))
    assert len(variants) == expected


def test_import_project(
    t4c8_instance: GPFInstance,
    t4c8_parquet_study: str,
    tmp_path: pathlib.Path,
) -> None:
    import_config = {
        "id": "test_parquet_study",
        "processing_config": {
            "work_dir": f"{tmp_path / 'work_dir'}",
        },
        "input": {
            "parquet": {
                "dir": t4c8_parquet_study,
            },
            "pedigree": {
                "file": "",
            },
        },
        "destination": {
            "storage_id": "internal",
        },
    }

    config_path = tmp_path / "import_project" / "import_config.yaml"

    setup_directories(
        config_path,
        yaml.dump(import_config))

    project = ImportProject.build_from_file(
        config_path, gpf_instance=t4c8_instance)

    assert len(t4c8_instance.get_genotype_data_ids()) == 5
    assert "test_parquet_study" not in t4c8_instance.get_genotype_data_ids()

    run_with_project(project)
    t4c8_instance.reload()

    assert len(t4c8_instance.get_genotype_data_ids()) == 5 + 1
    assert "test_parquet_study" in t4c8_instance.get_genotype_data_ids()

    study = t4c8_instance.get_genotype_data("test_parquet_study")
    assert len(list(study.query_variants())) == 12
