# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.parquet.partition_descriptor import PartitionDescriptor


def test_normalize_tblproperties() -> None:
    props_str = """
    [region_bin]
    chromosomes = chr1, chr2, chr3, chr4, chr5, chr6, chr7, chr8, chr9
    region_length = 30000000

    [family_bin]
    family_bin_size = 10

    [coding_bin]
    coding_effect_types = splice-site, frame-shift, nonsense, noStart, noEnd

    [frequency_bin]
    rare_boundary = 5
    """
    table_properties = PartitionDescriptor.parse_string(props_str).to_dict()

    assert table_properties["region_length"] == 30000000
    assert table_properties["chromosomes"] == [
        "chr1", "chr2", "chr3", "chr4", "chr5", "chr6", "chr7", "chr8", "chr9"
    ]
    assert table_properties["family_bin_size"] == 10
    assert table_properties["coding_effect_types"] == {
        "splice-site", "frame-shift", "nonsense", "noStart", "noEnd"
    }
    assert table_properties["rare_boundary"] == 5
