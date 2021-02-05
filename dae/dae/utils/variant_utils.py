"""
Created on Mar 5, 2018

@author: lubo
"""
import logging
import numpy as np

from dae.genome.genomes_db import Genome
from dae.variants.attributes import Sex


logger = logging.getLogger(__name__)


GENOTYPE_TYPE = np.int8
BEST_STATE_TYPE = np.int8


def mat2str(mat, col_sep="", row_sep="/"):
    return row_sep.join(
        [
            col_sep.join([str(n) if n >= 0 else "?" for n in mat[i, :]])
            for i in range(mat.shape[0])
        ]
    )


def str2mat(mat, col_sep="", row_sep="/"):
    if col_sep == "":
        return np.array(
            [[int(c) for c in r] for r in mat.split(row_sep)],
            dtype=GENOTYPE_TYPE,
        )
    return np.array(
        [[int(v) for v in r.split(col_sep)] for r in mat.split(row_sep)],
        dtype=GENOTYPE_TYPE,
    )


def best2gt(best_state):
    rows, cols = best_state.shape

    genotype = np.zeros(shape=(2, cols), dtype=GENOTYPE_TYPE)
    # genotype[1, :] = -2
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


def gt2str(gt):
    assert gt.shape[0] == 2
    result = []
    for i in range(gt.shape[1]):
        v0 = gt[0, i]
        v1 = gt[1, i]
        if v0 < 0:
            v0 = "."
        if v1 < 0:
            v1 = "."
        result.append(f"{v0}/{v1}")
    return ",".join(result)


def str2gt(gts):
    gts = gts.split(",")
    result = np.zeros(shape=(2,  len(gts)), dtype=GENOTYPE_TYPE)

    for col, pgts in enumerate(gts):
        vals = [
            int(p) if p != "." else -1 
            for p in pgts.split("/")
        ]
        result[0, col] = vals[0]
        result[1, col] = vals[1]
    return result


def reference_genotype(size):
    return np.zeros(shape=(2, size), dtype=GENOTYPE_TYPE)


def is_reference_genotype(gt):
    return np.any(gt == 0) and np.all(np.logical_or(gt == 0, gt == -1))


def is_all_reference_genotype(gt):
    return not np.any(gt != 0)


def is_unknown_genotype(gt):
    return np.any(gt == -1)


def is_all_unknown_genotype(gt):
    return np.all(gt == -1)


def trim_str_front(pos, ref, alt):
    assert alt, (pos, ref, alt)
    assert ref, (pos, ref, alt)

    n = 0
    for n, s in enumerate(zip(ref, alt)):
        if s[0] != s[1]:
            break

    if ref[n] == alt[n]:
        ref = ref[n + 1:]
        alt = alt[n + 1:]
        pos += n + 1
    else:
        ref = ref[n:]
        alt = alt[n:]
        pos += n

    if len(ref) == 0 or len(alt) == 0:
        return pos, ref, alt

    for n, s in enumerate(zip(ref[::-1], alt[::-1])):
        if s[0] != s[1]:
            break
    # not made simple
    if ref[-(n + 1)] == alt[-(n + 1)]:
        r, a = ref[: -(n + 1)], alt[: -(n + 1)]
    else:
        if n == 0:
            r, a = ref[:], alt[:]
        else:
            r, a = ref[:-n], alt[:-n]
    if len(r) == 0 or len(a) == 0:
        return pos, r, a

    return pos, r, a


def trim_str_back(pos, ref, alt):
    assert alt, (pos, ref, alt)
    assert ref, (pos, ref, alt)

    n = 0
    for n, s in enumerate(zip(ref[::-1], alt[::-1])):
        if s[0] != s[1]:
            break
    # not made simple
    if ref[-(n + 1)] == alt[-(n + 1)]:
        r, a = ref[: -(n + 1)], alt[: -(n + 1)]
    else:
        if n == 0:
            r, a = ref[:], alt[:]
        else:
            r, a = ref[:-n], alt[:-n]

    if len(r) == 0 or len(a) == 0:
        return pos, r, a

    for n, s in enumerate(zip(r, a)):
        if s[0] != s[1]:
            break

    if r[n] == a[n]:
        return pos + n + 1, r[n + 1:], a[n + 1:]

    return pos + n, r[n:], a[n:]


def cshl_format(pos, ref, alt, trimmer=trim_str_front):
    p, r, a = trimmer(pos, ref, alt)
    if len(r) == len(a) and len(r) == 0:
        # print('ref {:s} is the same as alt {:s}'.format(
        #     ref, alt), file=sys.stderr)
        return p, f"complex({r}->{a})", 0

    if len(r) == len(a) and len(r) == 1:
        wx = f"sub({r}->{a})"
        return p, wx, 1

    if len(r) > len(a) and len(a) == 0:
        wx = f"del({len(r)})"
        return p, wx, len(r)

    # len(ref) < len(alt):
    if len(r) < len(a) and len(r) == 0:
        wx = f"ins({a})"
        return p, wx, len(a)

    return p, f"complex({r}->{a})", max(len(r), len(a))


def vcf2cshl(pos, ref, alt, trimmer=trim_str_back):
    vp, vt, vl = cshl_format(pos, ref, alt, trimmer=trimmer)
    return vp, vt, vl


def get_locus_ploidy(
    chrom: str, pos: int, sex: Sex, genome: Genome
) -> int:
    if chrom in ("chrX", "X") and sex == Sex.M:
        if not genome.is_pseudoautosomal(chrom, pos):
            return 1
    return 2


def get_interval_locus_ploidy(
        chrom: str, pos_start: int, pos_end: int,
        sex: Sex, genome: Genome) -> int:

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


def liftover_variant(chrom, pos, ref, alt, lo, target_genome):
    lo_coordinates = lo.convert_coordinate(chrom, pos - 1)

    if not lo_coordinates:
        return None
    if len(lo_coordinates) > 1:
        logger.info(
            f"liftover_variant: liftover returns more than one target "
            f"position: {lo_coordinates}")

    lo_chrom, lo_pos, lo_strand, _ = lo_coordinates[0]

    if lo_strand == "+" or len(ref) == len(alt):
        lo_pos += 1
    elif lo_strand == "-":
        lo_pos -= len(ref)
        lo_pos -= 1

    _, tr_ref, tr_alt = trim_str_front(pos, ref, alt)

    lo_ref = target_genome.get_sequence(
        lo_chrom, lo_pos, lo_pos + len(ref) - 1)
    if lo_ref is None:
        logger.warning(
            f"can't find genomic sequence for {lo_chrom}:{lo_pos}")
        return None

    lo_alt = alt
    if lo_strand == "-":
        if not tr_alt:
            lo_alt = f"{lo_ref[0]}"
        else:
            lo_alt = reverse_complement(tr_alt)
            if not tr_ref:
                lo_alt = f"{lo_ref[0]}{lo_alt}"

    return (lo_chrom, lo_pos, lo_ref, lo_alt)
