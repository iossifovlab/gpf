# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pathlib
import pytest
from dae.utils.regions import Region
from dae.gpf_instance import GPFInstance
from dae.variants_loaders.parquet.loader import ParquetLoader
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.t4c8_import import t4c8_gpf
from dae.testing.acgt_import import acgt_gpf


@pytest.fixture(scope="module")
def t4c8_instance(tmp_path_factory: pytest.TempPathFactory) -> GPFInstance:
    root_path = tmp_path_factory.mktemp("t4c8_instance")
    gpf_instance = t4c8_gpf(root_path)
    return gpf_instance


@pytest.fixture(scope="module")
def acgt_instance(tmp_path_factory: pytest.TempPathFactory) -> GPFInstance:
    root_path = tmp_path_factory.mktemp("acgt_instance")
    gpf_instance = acgt_gpf(root_path)
    return gpf_instance


@pytest.fixture(scope="module")
def t4c8_study_nonpartitioned(t4c8_instance: GPFInstance) -> str:
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
def t4c8_study_partitioned(t4c8_instance: GPFInstance) -> str:
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


@pytest.fixture(scope="module")
def acgt_study_partitioned(acgt_instance: GPFInstance) -> str:
    root_path = pathlib.Path(acgt_instance.dae_dir)
    ped_path = setup_pedigree(
        root_path / "study_3" / "pedigree" / "in.ped",
        """
familyId personId dadId momId sex status role
f1.1     mom1     0     0     2   1      mom
f1.1     dad1     0     0     1   1      dad
f1.1     ch1      dad1  mom1  2   2      prb
        """)
    vcf_path1 = setup_vcf(
        root_path / "study_3" / "vcf" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
#CHROM POS  ID REF ALT  QUAL FILTER INFO FORMAT mom1 dad1 ch1
chr1   1    .  A   G,TA .    .      .    GT     0/1  0/1  0/0
chr1   25   .  C   C    .    .      .    GT     0/1  0/1  0/1
chr1   75   .  G   C,GA .    .      .    GT     0/1  0/2  0/2
chr2   1    .  A   G,TA .    .      .    GT     0/1  0/1  0/0
chr2   25   .  C   C    .    .      .    GT     0/1  0/1  0/1
chr2   75   .  G   C,GA .    .      .    GT     0/1  0/2  0/2
chr3   1    .  A   G,TA .    .      .    GT     0/1  0/1  0/0
chr3   25   .  C   C    .    .      .    GT     0/1  0/1  0/1
chr3   75   .  G   C,GA .    .      .    GT     0/1  0/2  0/2
        """)  # noqa

    project_config_update = {
        "partition_description": {
            "region_bin": {
                "chromosomes": ["chr1"],
                "region_length": 25,
            },
        },
    }
    vcf_study(
        root_path,
        "study_3", ped_path, [vcf_path1],
        acgt_instance,
        project_config_update=project_config_update,
        project_config_overwrite={"destination": {"storage_type": "schema2"}}
    )
    return f"{root_path}/work_dir/study_3"


def test_get_pq_filepaths_nonpartitioned(t4c8_study_nonpartitioned):
    loader = ParquetLoader(t4c8_study_nonpartitioned)
    summary_filepaths, family_filepaths = loader.get_pq_filepaths()
    assert list(map(os.path.basename, summary_filepaths)) == [
        "summary_bucket_index_100000.parquet"
    ]
    assert list(map(os.path.basename, family_filepaths)) == [
        "family_bucket_index_100000.parquet"
    ]


def test_get_pq_filepaths_partitioned(t4c8_study_partitioned):
    loader = ParquetLoader(t4c8_study_partitioned)
    summary_filepaths, family_filepaths = loader.get_pq_filepaths()
    assert set(map(os.path.basename, summary_filepaths)) == {
        "summary_region_bin_chr1_0_frequency_bin_1_coding_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "summary_region_bin_chr1_0_frequency_bin_2_coding_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "summary_region_bin_chr1_0_frequency_bin_3_coding_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "summary_region_bin_chr1_0_frequency_bin_3_coding_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "summary_region_bin_chr1_1_frequency_bin_1_coding_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "summary_region_bin_chr1_1_frequency_bin_2_coding_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "summary_region_bin_chr1_1_frequency_bin_2_coding_bin_1_bucket_index_100000.parquet",  # noqa: E501
    }
    assert set(map(os.path.basename, family_filepaths)) == {
        "family_region_bin_chr1_0_frequency_bin_1_coding_bin_0_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_0_frequency_bin_2_coding_bin_0_family_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_0_frequency_bin_2_coding_bin_0_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_0_frequency_bin_3_coding_bin_0_family_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_0_frequency_bin_3_coding_bin_0_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_0_frequency_bin_3_coding_bin_1_family_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_0_frequency_bin_3_coding_bin_1_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_1_frequency_bin_1_coding_bin_1_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_1_frequency_bin_2_coding_bin_0_family_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_1_frequency_bin_2_coding_bin_0_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_1_frequency_bin_2_coding_bin_1_family_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_1_frequency_bin_2_coding_bin_1_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
    }


def test_get_pq_filepaths_partitioned_region(t4c8_study_partitioned):
    loader = ParquetLoader(t4c8_study_partitioned)

    region = Region("chr1", 1, 100)
    summary_filepaths, family_filepaths = loader.get_pq_filepaths(region)
    assert set(map(os.path.basename, summary_filepaths)) == {
        "summary_region_bin_chr1_0_frequency_bin_1_coding_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "summary_region_bin_chr1_0_frequency_bin_2_coding_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "summary_region_bin_chr1_0_frequency_bin_3_coding_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "summary_region_bin_chr1_0_frequency_bin_3_coding_bin_0_bucket_index_100000.parquet",  # noqa: E501
    }
    assert set(map(os.path.basename, family_filepaths)) == {
        "family_region_bin_chr1_0_frequency_bin_1_coding_bin_0_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_0_frequency_bin_2_coding_bin_0_family_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_0_frequency_bin_2_coding_bin_0_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_0_frequency_bin_3_coding_bin_0_family_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_0_frequency_bin_3_coding_bin_0_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_0_frequency_bin_3_coding_bin_1_family_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_0_frequency_bin_3_coding_bin_1_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
    }

    region = Region("chr1", 101, 200)
    summary_filepaths, family_filepaths = loader.get_pq_filepaths(region)
    assert set(map(os.path.basename, summary_filepaths)) == {
        "summary_region_bin_chr1_1_frequency_bin_1_coding_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "summary_region_bin_chr1_1_frequency_bin_2_coding_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "summary_region_bin_chr1_1_frequency_bin_2_coding_bin_1_bucket_index_100000.parquet",  # noqa: E501
    }
    assert set(map(os.path.basename, family_filepaths)) == {
        "family_region_bin_chr1_1_frequency_bin_1_coding_bin_1_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_1_frequency_bin_2_coding_bin_0_family_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_1_frequency_bin_2_coding_bin_0_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_1_frequency_bin_2_coding_bin_1_family_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_1_frequency_bin_2_coding_bin_1_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
    }


def test_fetch_variants_count_nonpartitioned(t4c8_study_nonpartitioned):
    loader = ParquetLoader(t4c8_study_nonpartitioned)
    vs = list(loader.fetch_variants())
    # summary variants
    assert len(vs) == 3
    # family variants
    assert sum([len(fvs) for _, fvs in vs]) == 4


def test_fetch_variants_count_partitioned(t4c8_study_partitioned):
    loader = ParquetLoader(t4c8_study_partitioned)
    vs = list(loader.fetch_variants())
    # summary variants
    assert len(vs) == 6
    # family variants
    assert sum([len(fvs) for _, fvs in vs]) == 12


def test_fetch_variants_count_nonpartitioned_region(t4c8_study_nonpartitioned):
    loader = ParquetLoader(t4c8_study_nonpartitioned)
    vs = list(loader.fetch_variants(region="chr1:119"))
    # summary variants
    assert len(vs) == 1
    # family variants
    assert sum([len(fvs) for _, fvs in vs]) == 2

    vs = list(loader.fetch_variants(region="chr1:119-122"))
    # summary variants
    assert len(vs) == 2
    # family variants
    assert sum([len(fvs) for _, fvs in vs]) == 3


def test_fetch_variants_count_partitioned_region(t4c8_study_partitioned):
    loader = ParquetLoader(t4c8_study_partitioned)
    vs = list(loader.fetch_variants(region="chr1:1-89"))
    # summary variants
    assert len(vs) == 2
    # family variants
    assert sum([len(fvs) for _, fvs in vs]) == 4

    vs = list(loader.fetch_variants(region="chr1:90-200"))
    # summary variants
    assert len(vs) == 4
    # family variants
    assert sum([len(fvs) for _, fvs in vs]) == 8


def test_fetch_summary_variants_nonpartitioned(t4c8_study_nonpartitioned):
    loader = ParquetLoader(t4c8_study_nonpartitioned)
    vs = list(loader.fetch_summary_variants())
    assert len(vs) == 3


def test_fetch_summary_variants_partitioned(t4c8_study_partitioned):
    loader = ParquetLoader(t4c8_study_partitioned)
    vs = list(loader.fetch_summary_variants())
    assert len(vs) == 6


def test_fetch_summary_variants_nonpartitioned_region(
    t4c8_study_nonpartitioned
):
    loader = ParquetLoader(t4c8_study_nonpartitioned)
    vs = list(loader.fetch_summary_variants(region="chr1:119"))
    assert len(vs) == 1
    vs = list(loader.fetch_summary_variants(region="chr1:119-122"))
    assert len(vs) == 2


def test_fetch_summary_variants_partitioned_region(t4c8_study_partitioned):
    loader = ParquetLoader(t4c8_study_partitioned)
    vs = list(loader.fetch_summary_variants(region="chr1:1-89"))
    assert len(vs) == 2
    vs = list(loader.fetch_summary_variants(region="chr1:90-200"))
    assert len(vs) == 4


def test_fetch_variants_count_acgt(acgt_study_partitioned):
    loader = ParquetLoader(acgt_study_partitioned)
    assert len(list(loader.fetch_summary_variants())) == 9
    assert len(list(loader.fetch_summary_variants(region="chr1:1-100"))) == 3
    assert len(list(loader.fetch_summary_variants(region="other:1-100"))) == 6
    assert len(list(loader.fetch_summary_variants(region="chr2:1-100"))) == 3
    assert len(list(loader.fetch_summary_variants(region="chr3:1-100"))) == 3


def test_get_contigs_nonpartitioned(t4c8_study_nonpartitioned):
    loader = ParquetLoader(t4c8_study_nonpartitioned)
    assert loader.get_contigs() == {"chr1": 122}


def test_get_contigs_partitioned_no_other(t4c8_study_partitioned):
    loader = ParquetLoader(t4c8_study_partitioned)
    assert loader.get_contigs() == {"chr1": 200}


def test_get_contigs_partitioned_has_other(acgt_study_partitioned):
    loader = ParquetLoader(acgt_study_partitioned)
    assert loader.get_contigs() == {"chr1": 100, "other": 100}


def test_get_contigs_nonpartitioned_no_region_bins(
    mocker, acgt_study_partitioned
):
    loader = ParquetLoader(acgt_study_partitioned)
    mocker.patch.object(loader.partition_descriptor, "has_region_bins")
    loader.partition_descriptor.has_region_bins.return_value = False
    assert loader.get_contigs() is None
