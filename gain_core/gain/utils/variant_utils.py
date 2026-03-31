"""Pure string utilities for variant manipulation."""

DNA_COMPLEMENT_NUCLEOTIDES = {
    "A": "T",
    "C": "G",
    "G": "C",
    "T": "A",
    "N": "N",
}


def complement(nucleotides: str) -> str:
    return "".join(
        [
            DNA_COMPLEMENT_NUCLEOTIDES.get(n.upper(), "N")
            for n in nucleotides
        ])


def reverse_complement(nucleotides: str) -> str:
    return complement(nucleotides[::-1])


def trim_str_left(pos: int, ref: str, alt: str) -> tuple[int, str, str]:
    """Trim identical nucleotides prefixes and adjust position accordingly."""
    assert alt and ref, (pos, ref, alt)  # noqa PT018
    idx = 0
    for idx, sequence in enumerate(zip(ref, alt)):  # noqa B007
        if sequence[0] != sequence[1]:
            break

    if ref[idx] == alt[idx]:
        ref = ref[idx + 1:]
        alt = alt[idx + 1:]
        pos += idx + 1
    else:
        ref = ref[idx:]
        alt = alt[idx:]
        pos += idx

    return pos, ref, alt


def trim_str_right(pos: int, ref: str, alt: str) -> tuple[int, str, str]:
    """Trim identical nucleotides suffixes and adjust position accordingly."""
    assert alt, (pos, ref, alt)
    assert ref, (pos, ref, alt)

    idx = 0
    for idx, sequence in enumerate(zip(ref[::-1], alt[::-1])):  # noqa B007
        if sequence[0] != sequence[1]:
            break
    # not made simple
    if ref[-(idx + 1)] == alt[-(idx + 1)]:
        ref, alt = ref[: -(idx + 1)], alt[: -(idx + 1)]
    else:
        if idx == 0:
            ref, alt = ref[:], alt[:]
        else:
            ref, alt = ref[:-idx], alt[:-idx]

    return pos, ref, alt


def trim_str_left_right(pos: int, ref: str, alt: str) -> tuple[int, str, str]:
    if len(ref) == 0 or len(alt) == 0:
        return pos, ref, alt
    pos, ref, alt = trim_str_left(pos, ref, alt)
    if len(ref) == 0 or len(alt) == 0:
        return pos, ref, alt
    return trim_str_right(pos, ref, alt)


def trim_str_right_left(pos: int, ref: str, alt: str) -> tuple[int, str, str]:
    if len(ref) == 0 or len(alt) == 0:
        return pos, ref, alt
    pos, ref, alt = trim_str_right(pos, ref, alt)
    if len(ref) == 0 or len(alt) == 0:
        return pos, ref, alt
    return trim_str_left(pos, ref, alt)


def trim_parsimonious(pos: int, ref: str, alt: str) -> tuple[int, str, str]:
    """Trim identical nucleotides on both ends and adjust position."""
    assert alt, (pos, ref, alt)
    assert ref, (pos, ref, alt)

    r_pos, r_ref, r_alt = trim_str_right(pos, ref, alt)
    if len(r_ref) == 0:
        r_alt = alt[:len(r_alt) + 1]
        r_ref = ref[0:1]
        assert r_alt[-1] == r_ref[-1]
        return r_pos, r_ref, r_alt

    if len(r_alt) == 0:
        r_ref = ref[:len(r_ref) + 1]
        r_alt = alt[0:1]
        assert r_alt[-1] == r_ref[-1]
        return r_pos, r_ref, r_alt

    l_pos, l_ref, l_alt = trim_str_left(r_pos, r_ref, r_alt)
    if len(l_ref) == 0:
        l_ref = r_alt[-len(l_alt) - 1]
        l_alt = r_alt[-len(l_alt) - 1:]
        l_pos -= 1
        return l_pos, l_ref, l_alt
    if len(l_alt) == 0:
        l_alt = r_ref[-len(l_ref) - 1]
        l_ref = r_ref[-len(l_ref) - 1:]
        l_pos -= 1
        return l_pos, l_ref, l_alt

    return l_pos, l_ref, l_alt
