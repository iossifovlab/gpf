
def cnv_variant_type(variant):
    variant = variant.lower()
    if variant in {"cnv+", "duplication", "large_insertion", "gain"}:
        return "LARGE_DUPLICATION"
    if variant in {"cnv-", "deletion", "large_deletion", "loss"}:
        return "LARGE_DELETION"
    return None


def cshl2cnv_variant(location, variant, *args):
    # pylint: disable=unused-argument
    """Parse location and variant into CNV variant."""
    parts = location.split(":")
    if len(parts) != 2:
        raise ValueError(
            f"unexpected location format: "
            f"location={location}, variant=f{variant}")
    chrom, pos_range = parts
    parts = pos_range.split("-")
    if len(parts) != 2:
        raise ValueError(
            f"unexpected location format: "
            f"location={location}, variant=f{variant}")
    pos_begin, pos_end = parts
    variant_type = cnv_variant_type(variant)
    if variant_type is None:
        raise ValueError(f"unexpected CNV variant type: {variant}")
    return chrom, int(pos_begin), int(pos_end), variant_type
