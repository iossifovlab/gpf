from copy import deepcopy
import pytest
import os
from os.path import join
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.import_tools import import_tools
import pyarrow.parquet as pq


def test_import_task_bin_size(gpf_instance_2019, tmpdir):
    input_dir = join(
        os.path.dirname(os.path.realpath(__file__)),
        "resources", "import_task_bin_size")
    config_fn = join(input_dir, "import_config.yaml")

    import_config = GPFConfigParser.parse_and_interpolate_file(config_fn)
    import_config["processing_config"]["work_dir"] = str(tmpdir)

    project = import_tools.ImportProject.build_from_config(
        import_config, input_dir, gpf_instance=gpf_instance_2019)
    import_tools.run_with_project(project)

    files = os.listdir(tmpdir)
    assert "test_import_variants" in files

    variants_dir = join(tmpdir, "test_import_variants")
    regions_dirs = sorted(os.listdir(variants_dir))
    assert len(regions_dirs) == 4
    assert regions_dirs[0] == "_PARTITION_DESCRIPTION"
    assert regions_dirs[1] == "_VARIANTS_SCHEMA"
    assert regions_dirs[2] == "region_bin=1_0"
    assert regions_dirs[3] == "region_bin=1_1"

    out_dir = join(
        variants_dir,
        "region_bin=1_0/frequency_bin=0/family_bin=1")
    parquet_files = sorted(os.listdir(out_dir))
    assert len(parquet_files) == 3
    assert parquet_files[0] == "variants_region_bin_1_0_frequency_bin_0_" \
        "family_bin_1_bucket_index_0.parquet"
    assert parquet_files[1] == "variants_region_bin_1_0_frequency_bin_0_" \
        "family_bin_1_bucket_index_1.parquet"
    assert parquet_files[2] == "variants_region_bin_1_0_frequency_bin_0_" \
        "family_bin_1_bucket_index_3.parquet"

    _assert_variants(join(out_dir, parquet_files[0]), bucket_index=0,
                     positions=[123, 150, 30000000])
    _assert_variants(join(out_dir, parquet_files[1]), bucket_index=1,
                     positions=[30000001, 40000000])
    _assert_variants(join(out_dir, parquet_files[2]), bucket_index=3,
                     positions=[99999999])

    out_dir = join(
        variants_dir,
        "region_bin=1_1/frequency_bin=0/family_bin=0")
    parquet_files = sorted(os.listdir(out_dir))
    assert len(parquet_files) == 2
    assert parquet_files[0] == "variants_region_bin_1_1_frequency_bin_0_" \
        "family_bin_0_bucket_index_3.parquet"
    assert parquet_files[1] == "variants_region_bin_1_1_frequency_bin_0_" \
        "family_bin_0_bucket_index_4.parquet"

    _assert_variants(join(out_dir, parquet_files[0]), bucket_index=3,
                     positions=[120000000])
    _assert_variants(join(out_dir, parquet_files[1]), bucket_index=4,
                     positions=[120000001])

    out_dir = join(
        variants_dir,
        "region_bin=1_1/frequency_bin=0/family_bin=1")
    parquet_files = sorted(os.listdir(out_dir))
    assert len(parquet_files) == 1
    assert parquet_files[0] == "variants_region_bin_1_1_frequency_bin_0_" \
        "family_bin_1_bucket_index_3.parquet"
    _assert_variants(join(out_dir, parquet_files[0]), bucket_index=3,
                     positions=[100000000])


def _assert_variants(parquet_fn, bucket_index, positions):
    variants = pq.read_table(parquet_fn).to_pandas()
    assert variants.shape[0] == len(positions)
    assert (variants.bucket_index == bucket_index).all()
    assert (variants.position == positions).all()


def test_bucket_generation():
    import_config = dict(
        input=dict(
            pedigree=dict(
                file=join(_input_dir, "pedigree.ped"),
            ),
            denovo=dict(
                files=[join(_input_dir, "single_chromosome_variants.tsv")],
                person_id="spid",
                chrom="chrom",
                pos="pos",
                ref="ref",
                alt="alt",
            )
        ),
        processing_config=dict(
            work_dir="",
            denovo=dict(
                chromosomes=['1'],
                region_length=70_000_000
            )
        ),
        partition_description=dict(
            region_bin=dict(
                chromosomes=['1'],
                region_length=100_000_000
            )
        )
    )
    project = import_tools.ImportProject.build_from_config(import_config)
    buckets = list(project._loader_region_bins({}, "denovo"))
    assert len(buckets) == 4
    assert buckets[0].regions == ["1:1-70000000"]
    assert buckets[1].regions == ["1:70000001-140000000"]
    assert buckets[2].regions == ["1:140000001-210000000"]
    assert buckets[3].regions == ["1:210000001-249250621"]


def test_bucket_generation_chrom_mismatch(gpf_instance_short):
    import_config = dict(
        input=dict(
            pedigree=dict(
                file=join(_input_dir, "pedigree.ped"),
            ),
            denovo=dict(
                files=[join(_input_dir, "single_chromosome_variants.tsv")],
                person_id="spid",
                chrom="chrom",
                pos="pos",
                ref="ref",
                alt="alt",
            )
        ),
        processing_config=dict(
            work_dir="",
            denovo=dict(
                chromosomes=['2'],
                region_length=140_000
            )
        ),
        partition_description=dict(
            region_bin=dict(
                chromosomes=['1'],
                region_length=150_000
            )
        )
    )
    project = import_tools.ImportProject.build_from_config(
        import_config, gpf_instance=gpf_instance_short)
    buckets = list(project.get_import_variants_buckets())
    assert len(buckets) == 3
    for i in range(3):
        assert buckets[i].region_bin == f"other_{i}"
    assert buckets[0].regions == ["1:1-140000"]
    assert buckets[1].regions == ["1:140001-280000"]
    assert buckets[2].regions == ["1:280001-300000"]


_input_dir = join(
        os.path.dirname(os.path.realpath(__file__)),
        "resources", "import_task_bin_size")
_denovo_multi_chrom_config = dict(
    input=dict(
        pedigree=dict(
            file=join(_input_dir, "pedigree.ped")
        ),
        denovo=dict(
            files=[join(_input_dir, "multi_chromosome_variants.tsv")],
            person_id="spid",
            chrom="chrom",
            pos="pos",
            ref="ref",
            alt="alt",
        )
    ),
    processing_config=dict(
        work_dir="",
    ),
    partition_description=dict(
        region_bin=dict(
            chromosomes=['chr1'],
            region_length=100000000
        )
    )
)


@pytest.mark.parametrize("add_chrom_prefix", [None, "chr"])
def test_single_bucket_generation(add_chrom_prefix):
    import_config = deepcopy(_denovo_multi_chrom_config)
    import_config["processing_config"]["denovo"] = "single_bucket"
    if add_chrom_prefix:
        import_config["input"]["denovo"]["add_chrom_prefix"] = add_chrom_prefix
        prefix = add_chrom_prefix
    else:
        prefix = ""

    project = import_tools.ImportProject.build_from_config(import_config)
    buckets = list(project._loader_region_bins({}, "denovo"))
    assert len(buckets) == 1
    assert buckets[0].regions == [f"{prefix}1", f"{prefix}2", f"{prefix}3",
                                  f"{prefix}4", f"{prefix}5"]


def test_single_bucket_is_default_when_missing_processing_config():
    import_config = deepcopy(_denovo_multi_chrom_config)
    assert "denovo" not in import_config["processing_config"]

    project = import_tools.ImportProject.build_from_config(import_config)
    buckets = list(project._loader_region_bins({}, "denovo"))
    assert len(buckets) == 1
    assert buckets[0].regions == ["1", "2", "3", "4", "5"]


@pytest.mark.parametrize("add_chrom_prefix", [None, "chr"])
def test_chromosome_bucket_generation(add_chrom_prefix):
    import_config = deepcopy(_denovo_multi_chrom_config)
    import_config["processing_config"]["denovo"] = "chromosome"
    if add_chrom_prefix:
        import_config["input"]["denovo"]["add_chrom_prefix"] = add_chrom_prefix
        prefix = add_chrom_prefix
    else:
        prefix = ""

    project = import_tools.ImportProject.build_from_config(import_config)
    buckets = list(project._loader_region_bins({}, "denovo"))
    assert len(buckets) == 5
    assert buckets[0].regions == [f"{prefix}1"]
    assert buckets[1].regions == [f"{prefix}2"]
    assert buckets[2].regions == [f"{prefix}3"]
    assert buckets[3].regions == [f"{prefix}4"]
    assert buckets[4].regions == [f"{prefix}5"]


def test_chromosome_list_bucket_generation():
    import_config = deepcopy(_denovo_multi_chrom_config)
    import_config["processing_config"]["denovo"] = {
        "chromosomes": ["1", "2", "3"]
    }

    project = import_tools.ImportProject.build_from_config(import_config)
    buckets = list(project._loader_region_bins({}, "denovo"))
    assert len(buckets) == 4
    assert buckets[0].regions == ["1"]
    assert buckets[1].regions == ["2"]
    assert buckets[2].regions == ["3"]
    assert buckets[3].region_bin == "other_0"
    assert buckets[3].regions == ["4", "5"]
