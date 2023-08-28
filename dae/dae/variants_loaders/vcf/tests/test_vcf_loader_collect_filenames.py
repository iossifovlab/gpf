# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest
import pytest_mock

from dae.utils import fs_utils
from dae.variants_loaders.vcf.loader import VcfLoader
from dae.genomic_resources.testing import setup_vcf, \
    build_s3_test_filesystem, build_s3_test_bucket
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.testing.acgt_import import acgt_gpf


@pytest.fixture
def gpf_instance(
        tmp_path_factory: pytest.TempPathFactory) -> GPFInstance:
    root_path = tmp_path_factory.mktemp("instance")
    gpf_instance = acgt_gpf(root_path)
    return gpf_instance


@pytest.fixture
def vcf_vc_file(
    tmp_path_factory: pytest.TempPathFactory
) -> tuple[str, str, str]:
    root_path = tmp_path_factory.mktemp("vcf_vc")
    vcf1 = setup_vcf(root_path / "vcf_data" / "vcf_chr1.vcf.gz", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=chr1>
    #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT f1.mom
    chr1   4   .  C   T   .    .      .    GT     1/1
    """) # noqa
    vcf2 = setup_vcf(root_path / "vcf_data" / "vcf_chr2.vcf.gz", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=chr1>
    #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT f1.mom
    chr2   4   .  C   T   .    .      .    GT     1/1
    """) # noqa

    return str(root_path / "vcf_data"), str(vcf1), str(vcf2)


def test_collect_filenames_local(
    vcf_vc_file: tuple[str, str, str],
) -> None:
    base_path, vcf_chr1, vcf_chr2 = vcf_vc_file
    vcf_filenames = [fs_utils.join(base_path, "vcf_[vc].vcf.gz")]

    params = {
        "vcf_chromosomes": "chr1;chr2"
    }

    all_filenames, _ = VcfLoader._collect_filenames(params, vcf_filenames)

    assert len(all_filenames) == 2
    assert all_filenames[0] == vcf_chr1
    assert all_filenames[1] == vcf_chr2


def test_collect_filenames_s3(
    request: pytest.FixtureRequest,
    vcf_vc_file: tuple[str, str, str],
    mocker: pytest_mock.MockerFixture
) -> None:
    if not request.config.getoption("enable_s3"):
        pytest.skip("S3 unit testing not enabled.")

    _base_path, vcf_chr1, vcf_chr2 = vcf_vc_file

    s3_filesystem = build_s3_test_filesystem()
    s3_tmp_bucket_url = build_s3_test_bucket(s3_filesystem)

    base_path = fs_utils.join(s3_tmp_bucket_url, "vcf_dir")
    s3_filesystem.put(vcf_chr1, f"{base_path}/vcf_chr1.vcf.gz")
    s3_filesystem.put(vcf_chr2, f"{base_path}/vcf_chr2.vcf.gz")

    mocker.patch("dae.variants_loaders.vcf.loader.url_to_fs",
                 return_value=(s3_filesystem, None))

    vcf_filenames = [fs_utils.join(base_path, "vcf_[vc].vcf.gz")]
    params = {
        "vcf_chromosomes": "chr1;chr2"
    }
    all_filenames, _ = VcfLoader._collect_filenames(params, vcf_filenames)

    assert len(all_filenames) == 2
    assert all_filenames[0] == f"{base_path}/vcf_chr1.vcf.gz"
    assert all_filenames[1] == f"{base_path}/vcf_chr2.vcf.gz"
