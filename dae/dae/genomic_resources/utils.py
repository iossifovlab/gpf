

from collections.abc import Callable
from typing import Any, cast

from dae.genomic_resources.repository import GenomicResource


def build_chrom_mapping(
    resource: GenomicResource,
    config: dict[str, Any] | None = None,
) -> Callable[[str], str | None] | None:
    """Build chromosome mapping function from resource config.

    The resource config may contain `chrom_mapping` section with
    `filename`, `add_prefix` and `del_prefix` keys. The `filename` points
    to a file with two columns: original chromosome names and mapped names.

    These keys are mutually exclusive, only one of them may be present.

    Args:
        resource: genomic resource with config
    Returns:
        function that maps chromosome names or None if no mapping is defined
    """
    if config is None:
        config = resource.get_config()
    chrom_mapping_config = config.get("chrom_mapping")
    if chrom_mapping_config is None:
        return None

    filename = chrom_mapping_config.get("filename")

    if filename is not None:
        assert "add_prefix" not in chrom_mapping_config
        assert "del_prefix" not in chrom_mapping_config

        mapping = {}
        with resource.open_raw_file(filename) as f:
            for line in f:
                original, mapped = line.strip().split("\t")[:2]
                mapping[original] = mapped

        def map_chromosome(chrom: str) -> str | None:
            return mapping.get(chrom)

        return map_chromosome

    add_prefix = chrom_mapping_config.get("add_prefix")
    if add_prefix:
        assert "del_prefix" not in chrom_mapping_config

        def add_prefix_func(chrom: str) -> str:
            return f"{add_prefix}{chrom}"

        return add_prefix_func

    del_prefix = chrom_mapping_config.get("del_prefix")
    if del_prefix:
        def del_prefix_func(chrom: str) -> str:
            if chrom.startswith(del_prefix):
                return chrom[len(del_prefix):]
            return chrom
        return del_prefix_func

    mapping = chrom_mapping_config.get("mapping")
    if mapping:
        def chrom_mapping(chrom: str) -> str | None:
            return cast(str, mapping.get(chrom, chrom))

        return chrom_mapping

    raise ValueError(
        f"Invalid chrom_mapping configuration in: {resource.get_id()}")
