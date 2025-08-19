import re

from dae.annotation.annotatable import Annotatable


class Variant:
    """Provides variant defintion used in effect annotator."""

    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        chrom: str | None = None,
        position: int | None = None, *,
        loc: str | None = None,
        var: str | None = None,
        ref: str | None = None,
        alt: str | None = None,
        length: int | None = None,
        seq: str | None = None,
        variant_type: Annotatable.Type | None = None,
    ):

        self.variant_type = None
        self.length = None
        self.reference: str | None = None
        self.alternate: str | None = None
        self.set_position(chrom, position, loc)
        self.corrected_ref_position_last: int | None = None
        self.ref_position_last: int | None = None

        if variant_type in {
                Annotatable.Type.LARGE_DUPLICATION,
                Annotatable.Type.LARGE_DELETION}:
            assert self.chromosome is not None
            assert self.position is not None

            if self.length is None:
                assert length is not None
                self.length = length

            self.variant_type = variant_type
        else:
            self.set_ref_alt(var, ref, alt, length, seq, variant_type)
            assert self.reference is not None

            self.ref_position_last = self.position + len(self.reference)

            self.corrected_ref_position_last = max(
                self.position, self.ref_position_last - 1,
            )

    def set_position(
        self, chromosome: str | None,
        position: int | None,
        loc: str | None,
    ) -> None:
        """Set variant position."""
        if position is not None:
            assert chromosome is not None
            assert loc is None
            self.chromosome = chromosome
            self.position = int(position)

        if loc is not None:
            assert chromosome is None
            assert position is None
            chrom, loc_position = loc.split(":")
            self.chromosome = chrom
            if "-" not in loc_position:
                self.position = int(loc_position)
                self.length = None
            else:
                start, end = loc_position.split("-")
                self.position = int(start)
                self.length = int(end) - self.position

        assert self.chromosome is not None
        assert self.position is not None

    def set_ref_alt(
        self, var: str | None, ref: str | None, alt: str | None,
        _length: int | None, seq: str | None, _typ: Annotatable.Type | None,
    ) -> None:
        """Set variant reference and alternative."""
        if ref is not None:
            assert alt is not None
            assert var is None
            # assert length is None
            assert seq is None

            self.reference = ref
            self.alternate = alt

        if var is not None:
            assert ref is None
            assert alt is None
            # assert length is None
            assert seq is None

            self.set_ref_alt_from_variant(var)

        self.trim_equal_ref_alt_parts()
        assert self.reference is not None
        assert self.alternate is not None

    def trim_equal_ref_alt_parts(self) -> None:
        """Trim reference and alternative."""
        assert self.reference is not None
        assert self.alternate is not None
        start_index = -1
        for i in range(min(len(self.reference), len(self.alternate))):
            if self.reference[i] == self.alternate[i]:
                start_index = i
            else:
                break

        self.reference = self.reference[start_index + 1:]
        self.alternate = self.alternate[start_index + 1:]
        self.position += start_index + 1

    def set_ref_alt_from_variant(self, var: str) -> None:
        """Set reference and alternative from CSHL variant."""
        if var.startswith("complex"):
            res = re.match(r".*\((.*)->(.*)\)", var)
            assert res is not None
            self.reference = res.group(1).upper()
            self.alternate = res.group(2).upper()
            return

        var_type = var[0].upper()
        if var_type == "S":
            res = re.match(r".*\((.*)->(.*)\)", var)
            assert res is not None
            self.reference = res.group(1).upper()
            self.alternate = res.group(2).upper()
            return

        if var_type == "D":
            res = re.match(r".*\((.*)\)", var)
            assert res is not None
            self.reference = "0" * int(res.group(1))
            self.alternate = ""
            return

        if var_type == "I":
            res = re.match(r".*\((.*)\)", var)
            assert res is not None
            self.reference = ""
            self.alternate = re.sub(r"[0-9]+", "", res.group(1).upper())
            return

        raise ValueError(f"Unknown variant!: {var}")
