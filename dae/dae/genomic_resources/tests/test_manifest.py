"""Test manifest utils."""

from dae.genomic_resources.repository import ManifestEntry


def test_manifest_entry_timestamps_zero():
    """Test timestamps handling for UNIX epoch beginning."""

    entry = ManifestEntry(
        "test", 1, ManifestEntry.convert_timestamp(0), None)
    
    assert entry.time == "1970-01-01T00:00:00+00:00"
    assert entry.get_timestamp() == 0
