import logging

import numpy as np
import numpy.typing as npt

from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.variants.attributes import Sex

logger = logging.getLogger(__name__)


GenotypeType = np.int8
BestStateType = np.int8


def mat2str(mat: np.ndarray, col_sep: str = "", row_sep: str = "/") -> str:
    return row_sep.join(
        [
            col_sep.join([str(n) if n >= 0 else "?" for n in mat[i, :]])
            for i in range(mat.shape[0])
        ],
    )


def str2mat(
        mat: str, col_sep: str = "", row_sep: str = "/",
        dtype: npt.DTypeLike = GenotypeType) -> np.ndarray:
    """Convert a string into a numpy matrix."""
    if col_sep == "":
        return np.array(
            [[int(c) for c in r] for r in mat.split(row_sep)],
            dtype=dtype,
        )
    return np.array(
        [[int(v) for v in r.split(col_sep)] for r in mat.split(row_sep)],
        dtype=dtype,
    )


def str2mat_adjust_colsep(mat: str) -> np.ndarray:
    """Convert a string into a numpy matrix."""
    col_sep = ""
    if " " in mat:
        col_sep = " "
    return str2mat(mat, col_sep=col_sep)


def best2gt(
        best_state: np.ndarray,
        dtype: npt.DTypeLike = GenotypeType) -> np.ndarray:
    """Convert a best state array to a genotype array."""
    rows, cols = best_state.shape

    genotype = np.zeros(shape=(2, cols), dtype=dtype)
    ploidy = np.sum(best_state, 0)
    for allele_index in range(rows):
        best_state_row = best_state[allele_index, :]
        for col in range(cols):
            if best_state_row[col] == 2:
                genotype[:, col] = allele_index
            elif best_state_row[col] == 1:
                if genotype[0, col] == 0:
                    genotype[0, col] = allele_index
                    if ploidy[col] == 1:
                        genotype[1, col] = -2
                else:
                    genotype[1, col] = allele_index

    return genotype


def fgt2str(family_genotypes: np.ndarray, sep: str = ";") -> str:
    """Convert a family genotype array to a string."""
    result = []
    for genotype in family_genotypes:
        v_0 = genotype[0]
        v_1 = genotype[1]
        if v_0 < 0:
            v_0 = "."
        if v_1 < 0:
            v_1 = "."
        result.append(f"{v_0}/{v_1}")
    return sep.join(result)


def str2fgt(fgt: str) -> np.ndarray:
    """Convert a string to a family genotype array."""
    cols = fgt.split(";")
    result = np.zeros(shape=(2, len(cols)), dtype=GenotypeType)
    for idx, col in enumerate(cols):
        tokens = col.split("/")

        v_0 = -1 if tokens[0] == "." else int(tokens[0])
        v_1 = -1 if tokens[1] == "." else int(tokens[1])

        result[0][idx] = v_0
        result[1][idx] = v_1

    return result


def gt2str(gt: np.ndarray) -> str:
    """Convert a genotype array to a string."""
    assert gt.shape[0] == 2
    result = []
    for i in range(gt.shape[1]):
        v_0 = gt[0, i]
        v_1 = gt[1, i]
        if v_0 < 0:
            v_0 = "."
        if v_1 < 0:
            v_1 = "."
        result.append(f"{v_0}/{v_1}")
    return ",".join(result)


def str2gt(
        genotypes: str, split: str = ",",
        dtype: npt.DTypeLike = GenotypeType) -> np.ndarray:
    """Convert a string to a genotype array."""
    gts = genotypes.split(split)
    result = np.zeros(shape=(2, len(gts)), dtype=dtype)

    for col, pgts in enumerate(gts):
        vals = [
            int(p) if p != "." else -1
            for p in pgts.split("/")
        ]
        result[0, col] = vals[0]
        result[1, col] = vals[1]
    return result


def reference_genotype(size: int) -> np.ndarray:
    return np.zeros(shape=(2, size), dtype=GenotypeType)


def is_reference_genotype(gt: np.ndarray) -> bool:
    return bool(np.any(gt == 0) and np.all(np.logical_or(gt == 0, gt == -1)))


def is_all_reference_genotype(gt: np.ndarray) -> bool:
    return not np.any(gt != 0)


def is_unknown_genotype(gt: np.ndarray) -> bool:
    return bool(np.any(gt == -1))


def is_all_unknown_genotype(gt: np.ndarray) -> bool:
    return bool(np.all(gt == -1))


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


def get_locus_ploidy(
        chrom: str, pos: int, sex: Sex, genome: ReferenceGenome) -> int:

    if chrom in ("chrX", "X") and sex == Sex.M and \
            not genome.is_pseudoautosomal(chrom, pos):
        return 1
    return 2


def get_interval_locus_ploidy(
        chrom: str, pos_start: int, pos_end: int,
        sex: Sex, genome: ReferenceGenome) -> int:

    start_ploidy = get_locus_ploidy(chrom, pos_start, sex, genome)
    end_ploidy = get_locus_ploidy(chrom, pos_end, sex, genome)
    return max(start_ploidy, end_ploidy)


DNA_COMPLEMENT_NUCLEOTIDES = {
    "A": "T",
    "T": "A",
    "G": "C",
    "C": "G",
}


def complement(nucleotides: str) -> str:
    return "".join(
        [
            DNA_COMPLEMENT_NUCLEOTIDES.get(n.upper(), n)
            for n in nucleotides
        ])


def reverse_complement(nucleotides: str) -> str:
    return complement(nucleotides[::-1])
