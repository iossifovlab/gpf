import pathlib
import pytest

from dae.gpf_instance import GPFInstance
from dae.variants_loaders.parquet.loader import ParquetLoader
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.t4c8_import import t4c8_gpf


@pytest.fixture(scope="module")
def t4c8_instance(tmp_path_factory: pytest.TempPathFactory) -> GPFInstance:
    root_path = tmp_path_factory.mktemp("t4c8_instance")
    gpf_instance = t4c8_gpf(root_path)
    return gpf_instance


@pytest.fixture(scope="module")
def t4c8_study_1(t4c8_instance: GPFInstance) -> str:
    root_path = pathlib.Path(t4c8_instance.dae_dir)
    ped_path = setup_pedigree(
        root_path / "study_1" / "pedigree" / "in.ped",
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
        root_path / "study_1" / "vcf" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
##contig=<ID=chr3>
#CHROM POS  ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 ch1 mom3 dad3 ch3
chr1   54   .  T   C   .    .      .    GT     0/1  0/0  0/1 0/0  0/0  0/0
chr1   119  .  A   G,C .    .      .    GT     0/0  0/2  0/2 0/1  0/2  0/1
chr1   122  .  A   C   .    .      .    GT     0/0  1/0  0/0 0/0  0/0  0/0
        """)  # noqa

    vcf_study(
        root_path,
        "study_1", ped_path, [vcf_path1],
        t4c8_instance,
        project_config_overwrite={"destination": {"storage_type": "schema2"}}
    )
    return f"{root_path}/work_dir/study_1"


@pytest.fixture(scope="module")
def t4c8_study_2(t4c8_instance: GPFInstance) -> str:
    root_path = pathlib.Path(t4c8_instance.dae_dir)
    ped_path = setup_pedigree(
        root_path / "study_2" / "pedigree" / "in.ped",
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
        root_path / "study_2" / "vcf" / "in.vcf.gz",
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
        """)  # noqa

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
                ]
            },
            "family_bin": {
                "family_bin_size": 2,
            }
        },
    }
    vcf_study(
        root_path,
        "study_2", ped_path, [vcf_path1],
        t4c8_instance,
        project_config_update=project_config_update,
        project_config_overwrite={"destination": {"storage_type": "schema2"}}
    )
    return f"{root_path}/work_dir/study_2"


def test_fetch_variants_count_nonpartitioned(t4c8_study_1):
    loader = ParquetLoader(t4c8_study_1)
    loader.load_families()
    vs = list(loader.fetch_variants())
    # summary variants
    assert len(vs) == 3
    # family variants
    assert sum([len(fvs) for _, fvs in vs]) == 4


def test_fetch_variants_count_partitioned(t4c8_study_2):
    loader = ParquetLoader(t4c8_study_2, partitioned=True)
    loader.load_families()
    vs = list(loader.fetch_variants())
    # summary variants
    assert len(vs) == 6
    # family variants
    assert sum([len(fvs) for _, fvs in vs]) == 12