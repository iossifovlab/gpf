import pytest

from dae.genome.genome_access import GenomicSequence

from dae.backends.impala.parquet_io import ParquetPartitionDescriptor
from dae.backends.impala.import_commons import MakefilePartitionHelper


@pytest.mark.parametrize(
    "region_length,chrom,bins_count",
    [
        (3_000_000_000, "1", 1),
        (3_000_000_000, "2", 1),
        (300_000_000, "1", 1),
        (300_000_000, "2", 1),
        (245_000_000, "1", 2),
        (245_000_000, "2", 1),
        (243_000_000, "2", 2),
        (243_199_373, "2", 1),
        (249_250_621, "1", 1),
    ],
)
def test_target_generator_region_bins_count(
    region_length, chrom, bins_count, genomes_db_2019
):

    partition_descriptor = ParquetPartitionDescriptor(
        ["1", "2"], region_length
    )

    generator = MakefilePartitionHelper(
        partition_descriptor, genomes_db_2019.get_genomic_sequence()
    )
    assert generator is not None
    assert generator.region_bins_count(chrom) == bins_count


@pytest.mark.parametrize(
    "region_length,chrom,targets",
    [
        (3_000_000_000, "1", [("1_0", "1")]),
        (3_000_000_000, "3", [("other_0", "3")]),
        (3_000_000_000, "X", [("other_0", "X")]),
        (198_022_430, "3", [("other_0", "3")]),
        (
            100_000_000,
            "3",
            [
                ("other_0", "3:1-100000000"),
                ("other_1", "3:100000001-198022430"),
            ],
        ),
    ],
)
def test_target_generator_region_bins(
    region_length, chrom, targets, genomes_db_2019
):

    partition_descriptor = ParquetPartitionDescriptor(
        ["1", "2"], region_length
    )

    generator = MakefilePartitionHelper(
        partition_descriptor, genomes_db_2019.get_genomic_sequence()
    )

    assert generator is not None
    result = generator.generate_chrom_targets(chrom)
    print(result)
    assert targets == result


@pytest.mark.parametrize(
    "region_length,target_chroms,targets",
    [
        (3_000_000_000, ("1", "2", "3"), ["3"]),
        (3_000_000_000, ("3",), ["3"]),
        (3_000_000_000, ("3", "X"), ["3", "X"]),
        (3_000_000, ("3", "X"), ["3:1-3000000", "X:1-3000000"]),
    ],
)
def test_target_generator_other_0(
    region_length, target_chroms, targets, genomes_db_2019
):

    partition_descriptor = ParquetPartitionDescriptor(
        ["1", "2"], region_length
    )

    generator = MakefilePartitionHelper(
        partition_descriptor, genomes_db_2019.get_genomic_sequence()
    )

    result = generator.generate_variants_targets(target_chroms)
    print(result)
    assert result["other_0"] == targets


@pytest.mark.parametrize(
    "region_length,targets",
    [
        (3_000_000_000, set(["1_0"])),
        (300_000_000, set(["1_0"])),
        (200_000_000, set(["1_0", "1_1"])),
        (50_000_000, set(["1_0", "1_1", "1_2", "1_3", "1_4"])),
    ],
)
def test_target_generator_chrom_1(region_length, targets, genomes_db_2019):

    partition_descriptor = ParquetPartitionDescriptor(
        ["1", "2"], region_length
    )

    generator = MakefilePartitionHelper(
        partition_descriptor, genomes_db_2019.get_genomic_sequence()
    )

    result = generator.generate_variants_targets(["1"])
    print(result)
    assert set(result.keys()) == targets


@pytest.mark.parametrize(
    "region_length,targets",
    [
        (3_000_000_000, set(["other_0"])),
        (300_000_000, set(["other_0"])),
        (190_000_000, set(["other_0", "other_1"])),
        (50_000_000, set(["other_0", "other_1", "other_2", "other_3"])),
    ],
)
def test_target_generator_chrom_other(region_length, targets, genomes_db_2019):

    partition_descriptor = ParquetPartitionDescriptor(
        ["1", "2"], region_length
    )

    generator = MakefilePartitionHelper(
        partition_descriptor, genomes_db_2019.get_genomic_sequence()
    )
    print(generator.chromosome_lengths)

    result = generator.generate_variants_targets(["3", "4"])
    print(result)
    assert set(result.keys()) == targets


@pytest.mark.parametrize(
    "region_length,targets",
    [
        (3_000_000_000, set(["other_0"])),
        (300_000_000, set(["other_0", "other_1"])),
        (150_000_000, set(["other_0", "other_1", "other_2"])),
        (100_000_000, set(["other_0", "other_1", "other_2", "other_3"])),
    ],
)
def test_target_generator_chrom_prefix_target_other(
    region_length, targets, genomes_db_2019, mocker
):

    mocker.patch.object(
        GenomicSequence,
        "get_all_chrom_lengths",
        return_value=[
            ("chr1", 100_000_000),
            ("chr2", 200_000_000),
            ("chr3", 300_000_000),
            ("chr4", 400_000_000),
        ],
    )

    partition_descriptor = ParquetPartitionDescriptor(
        ["chr1", "chr2"], region_length
    )

    generator = MakefilePartitionHelper(
        partition_descriptor,
        genomes_db_2019.get_genomic_sequence(),
        add_chrom_prefix="chr",
    )
    print(generator.chromosome_lengths)
    assert len(generator.chromosome_lengths) == 4

    result = generator.generate_variants_targets(["3", "4"])
    print(result)
    assert set(result.keys()) == targets
    for regions in result.values():
        for region in regions:
            print(region)
            assert "chr" not in region


@pytest.mark.parametrize(
    "region_length,targets",
    [
        (3_000_000_000, set(["chr1_0", "chr2_0"])),
        (150_000_000, set(["chr1_0", "chr2_0", "chr2_1"])),
        (90_000_000, set(["chr1_0", "chr1_1", "chr2_0", "chr2_1", "chr2_2"])),
    ],
)
def test_target_generator_add_chrom_prefix_target_chrom(
    region_length, targets, genomes_db_2019, mocker
):

    mocker.patch.object(
        GenomicSequence,
        "get_all_chrom_lengths",
        return_value=[
            ("chr1", 100_000_000),
            ("chr2", 200_000_000),
            ("chr3", 300_000_000),
            ("chr4", 400_000_000),
        ],
    )

    partition_descriptor = ParquetPartitionDescriptor(
        ["chr1", "chr2"], region_length
    )

    generator = MakefilePartitionHelper(
        partition_descriptor,
        genomes_db_2019.get_genomic_sequence(),
        add_chrom_prefix="chr",
    )
    print(generator.chromosome_lengths)
    assert len(generator.chromosome_lengths) == 4

    result = generator.generate_variants_targets(["1", "2"])
    print(result)
    assert set(result.keys()) == targets
    for regions in result.values():
        for region in regions:
            print(region)
            assert "chr" not in region


@pytest.mark.parametrize(
    "region_length,targets",
    [
        (3_000_000_000, set(["1_0", "2_0"])),
        (150_000_000, set(["1_0", "2_0", "2_1"])),
        (90_000_000, set(["1_0", "1_1", "2_0", "2_1", "2_2"])),
    ],
)
def test_target_generator_del_chrom_prefix_target_chrom(
    region_length, targets, genomes_db_2019, mocker
):

    mocker.patch.object(
        GenomicSequence,
        "get_all_chrom_lengths",
        return_value=[
            ("1", 100_000_000),
            ("2", 200_000_000),
            ("3", 300_000_000),
            ("4", 400_000_000),
        ],
    )

    partition_descriptor = ParquetPartitionDescriptor(
        ["1", "2"], region_length
    )

    generator = MakefilePartitionHelper(
        partition_descriptor,
        genomes_db_2019.get_genomic_sequence(),
        del_chrom_prefix="chr",
    )
    print(generator.chromosome_lengths)
    assert len(generator.chromosome_lengths) == 4

    result = generator.generate_variants_targets(["1", "2"])
    print(result)
    assert set(result.keys()) == targets
    # for regions in result.values():
    #     for region in regions:
    #         print(region)


@pytest.mark.parametrize(
    "region_length,targets",
    [
        (3_000_000_000, [("chr1_0", 0), ("chr2_0", 1), ("other_0", 2)]),
        (
            150_000_000,
            [
                ("chr1_0", 0),
                ("chr2_0", 1),
                ("chr2_1", 2),
                ("other_0", 3),
                ("other_1", 4),
                ("other_2", 5),
            ],
        ),
        (
            100_000_000,
            [
                ("chr1_0", 0),
                ("chr2_0", 1),
                ("chr2_1", 2),
                ("other_0", 3),
                ("other_1", 4),
                ("other_2", 5),
                ("other_3", 6),
            ],
        ),
    ],
)
def test_makefile_generator_bucket_numbering(
    region_length, targets, genomes_db_2019, mocker
):

    mocker.patch.object(
        GenomicSequence,
        "get_all_chrom_lengths",
        return_value=[
            ("chr1", 100_000_000),
            ("chr2", 200_000_000),
            ("chr3", 300_000_000),
            ("chr4", 400_000_000),
        ],
    )

    partition_descriptor = ParquetPartitionDescriptor(
        ["chr1", "chr2"], region_length
    )

    generator = MakefilePartitionHelper(
        partition_descriptor,
        genomes_db_2019.get_genomic_sequence(),
        add_chrom_prefix="chr",
    )
    print(generator.chromosome_lengths)
    assert len(generator.chromosome_lengths) == 4

    for (region_bin, bucket_index) in targets:
        assert bucket_index == generator.bucket_index(region_bin)


@pytest.mark.parametrize(
    "region_length,targets",
    [
        (
            3_000_000_000,
            [
                ("chr1_0", ["chr1"]),
                ("chr2_0", ["chr2"]),
                ("other_0", ["chr3", "chr4"]),
            ],
        ),
        (
            150_000_000,
            [
                ("chr1_0", ["chr1"]),
                ("chr2_0", ["chr2:1-150000000"]),
                ("chr2_1", ["chr2:150000001-200000000"]),
                ("other_0", ["chr3:1-150000000", "chr4:1-150000000"]),
                (
                    "other_1",
                    ["chr3:150000001-300000000", "chr4:150000001-300000000"],
                ),
                ("other_2", ["chr4:300000001-400000000"]),
            ],
        ),
    ],
)
def test_makefile_generator_regions(
    region_length, targets, genomes_db_2019, mocker
):

    mocker.patch.object(
        GenomicSequence,
        "get_all_chrom_lengths",
        return_value=[
            ("chr1", 100_000_000),
            ("chr2", 200_000_000),
            ("chr3", 300_000_000),
            ("chr4", 400_000_000),
        ],
    )

    partition_descriptor = ParquetPartitionDescriptor(
        ["chr1", "chr2"], region_length
    )

    generator = MakefilePartitionHelper(
        partition_descriptor, genomes_db_2019.get_genomic_sequence()
    )

    print(generator.chromosome_lengths)
    assert len(generator.chromosome_lengths) == 4

    variants_targets = generator.generate_variants_targets(
        ["chr1", "chr2", "chr3", "chr4"]
    )

    for (region_bin, regions) in targets:
        assert region_bin in variants_targets
        assert regions == variants_targets[region_bin]


@pytest.mark.parametrize(
    "region_length,targets",
    [
        (
            3_000_000_000,
            [
                ("1_0", ["chr1"]),
                ("2_0", ["chr2"]),
                ("other_0", ["chr3", "chr4"]),
            ],
        ),
        (
            150_000_000,
            [
                ("1_0", ["chr1"]),
                ("2_0", ["chr2:1-150000000"]),
                ("2_1", ["chr2:150000001-200000000"]),
                ("other_0", ["chr3:1-150000000", "chr4:1-150000000"]),
                (
                    "other_1",
                    ["chr3:150000001-300000000", "chr4:150000001-300000000"],
                ),
                ("other_2", ["chr4:300000001-400000000"]),
            ],
        ),
    ],
)
def test_makefile_generator_regions_del_chrom_prefix(
    region_length, targets, genomes_db_2019, mocker
):

    mocker.patch.object(
        GenomicSequence,
        "get_all_chrom_lengths",
        return_value=[
            ("1", 100_000_000),
            ("2", 200_000_000),
            ("3", 300_000_000),
            ("4", 400_000_000),
        ],
    )

    partition_descriptor = ParquetPartitionDescriptor(
        ["1", "2"], region_length
    )

    generator = MakefilePartitionHelper(
        partition_descriptor,
        genomes_db_2019.get_genomic_sequence(),
        del_chrom_prefix="chr",
    )

    print(generator.chromosome_lengths)
    assert len(generator.chromosome_lengths) == 4

    variants_targets = generator.generate_variants_targets(
        ["chr1", "chr2", "chr3", "chr4"]
    )

    for (region_bin, regions) in targets:
        assert region_bin in variants_targets
        assert regions == variants_targets[region_bin]


@pytest.mark.parametrize(
    "region_length,targets",
    [
        (
            3_000_000_000,
            [("chr1_0", ["1"]), ("chr2_0", ["2"]), ("other_0", ["3", "4"])],
        ),
        (
            150_000_000,
            [
                ("chr1_0", ["1"]),
                ("chr2_0", ["2:1-150000000"]),
                ("chr2_1", ["2:150000001-200000000"]),
                ("other_0", ["3:1-150000000", "4:1-150000000"]),
                (
                    "other_1",
                    ["3:150000001-300000000", "4:150000001-300000000"],
                ),
                ("other_2", ["4:300000001-400000000"]),
            ],
        ),
    ],
)
def test_makefile_generator_regions_add_chrom_prefix(
    region_length, targets, genomes_db_2019, mocker
):

    mocker.patch.object(
        GenomicSequence,
        "get_all_chrom_lengths",
        return_value=[
            ("chr1", 100_000_000),
            ("chr2", 200_000_000),
            ("chr3", 300_000_000),
            ("chr4", 400_000_000),
        ],
    )

    partition_descriptor = ParquetPartitionDescriptor(
        ["chr1", "chr2"], region_length
    )

    generator = MakefilePartitionHelper(
        partition_descriptor,
        genomes_db_2019.get_genomic_sequence(),
        add_chrom_prefix="chr",
    )

    print(generator.chromosome_lengths)
    assert len(generator.chromosome_lengths) == 4

    variants_targets = generator.generate_variants_targets(
        ["1", "2", "3", "4"]
    )

    for (region_bin, regions) in targets:
        assert region_bin in variants_targets
        assert regions == variants_targets[region_bin]
