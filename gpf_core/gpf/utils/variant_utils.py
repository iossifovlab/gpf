import logging
import math
from enum import Enum

import numpy as np
import numpy.typing as npt

from gain.genomic_resources.reference_genome import ReferenceGenome
from gain.utils.variant_utils import (  # noqa: F401
    DNA_COMPLEMENT_NUCLEOTIDES,
    complement,
    reverse_complement,
    trim_parsimonious,
    trim_str_left,
    trim_str_left_right,
    trim_str_right,
    trim_str_right_left,
)
from gpf.variants.attributes import Sex

logger = logging.getLogger(__name__)


GenotypeType = np.int8
BestStateType = np.int8


def mat2str(
    mat: np.ndarray | list[list[int]],
    col_sep: str = "", row_sep: str = "/",
) -> str:
    """Construct sting representation of a matrix."""
    if isinstance(mat, np.ndarray):
        return row_sep.join(
            [
                col_sep.join([str(n) if n >= 0 else "?" for n in mat[i, :]])
                for i in range(mat.shape[0])
            ],
        )
    return row_sep.join(
        [
            col_sep.join([str(n) if int(n) >= 0 else "?" for n in mat[i]])
            for i in range(len(mat))
        ],
    )


def str2lists(
    mat: str, col_sep: str = "", row_sep: str = "/",
) -> list[list[int]]:
    """Convert a string into a numpy matrix."""
    if col_sep == "":
        return [[int(c) for c in r] for r in mat.split(row_sep)]

    return [
        [int(v) for v in r.split(col_sep)] for r in mat.split(row_sep)]


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


def get_locus_ploidy(
    chrom: str, pos: int, sex: Sex, genome: ReferenceGenome,
) -> int:
    """Return the number of ploidy at a given position in a chromosome."""
    if chrom == "Y" and sex == Sex.F:
        logger.error("Chromosome Y identified for a female individual!")
        return 0

    if chrom in ("chrX", "X", "chrY", "Y") \
            and sex in (Sex.M, Sex.U) \
            and not genome.is_pseudoautosomal(chrom, pos):
        return 1
    return 2


def get_interval_locus_ploidy(
        chrom: str, pos_start: int, pos_end: int,
        sex: Sex, genome: ReferenceGenome) -> int:

    start_ploidy = get_locus_ploidy(chrom, pos_start, sex, genome)
    end_ploidy = get_locus_ploidy(chrom, pos_end, sex, genome)
    return max(start_ploidy, end_ploidy)


class BitmaskEnumTranslator:
    """
    Encoder and decoder of two enums into a single value.

    It has two enum types: the main and the partition by enum.
    For every enum value in the partition_by enum,
    a tuple of bits corresponding to the main enum will be added to the value.
    The amount of bits in the tuple will depend on how many bitwise values
    the main enum holds. The amount of tuples depends on the amount of bitwise
    values the partition by holds.

    Enums provided to this class must have bitwise values, behavior with
    enums without bitwise values is undefined.
    """
    def __init__(
        self, *,
        main_enum_type: type[Enum],
        partition_by_enum_type: type[Enum],
    ):

        self.main_enum_type = main_enum_type
        self.partition_by_enum_type = partition_by_enum_type
        self.main_indexes = {}
        self.partition_indexes: dict = {}

        main_enumerations = {
            e.name: e.value for e in list(main_enum_type)
            if e.value != 0
        }

        for name, value in main_enumerations.items():
            if value == 0:
                continue
            value_bit = math.log2(value)
            if not value_bit.is_integer():
                raise ValueError(
                    f"Encountered an invalid bitmask value {value} "
                    f"in enum {self.partition_by_enum_type}",
                )
            self.main_indexes[name] = int(value_bit)

        self.tuple_length = max(self.main_indexes.values()) + 1

        partition_enumerations = {
            e.name: e.value for e in list(partition_by_enum_type)
        }
        self.partition_indexes = {}

        for name, value in partition_enumerations.items():
            if value == 0:
                raise ValueError(
                    "Cannot create translator partitioning for enum"
                    "if a partitioning value is 0",
                )
            value_bit = math.log2(value)
            if not value_bit.is_integer():
                raise ValueError(
                    f"Encountered an invalid bitmask value {value} "
                    f"in enum {self.partition_by_enum_type}",
                )
            self.partition_indexes[name] = int(value_bit)

        self.partitions_count = max(self.partition_indexes.values()) + 1
        self.total_bits = self.tuple_length * self.partitions_count

        if self.total_bits > 64:
            logger.warning(
                "Created bitwise translator with values larger than 64 bits!",
            )

    def apply_mask(
        self, mask: int, main_enum_value: int, partition_by_enum: Enum,
    ) -> int:
        """
        Apply a mask filter over an existing mask and return the new mask.
        """
        if not isinstance(partition_by_enum, self.partition_by_enum_type):
            raise TypeError(
                f"{partition_by_enum} is a different enum type!"
                f"Expected {self.partition_by_enum_type}",
            )

        bitshift_amount = \
            self.partition_indexes[partition_by_enum.name] * self.tuple_length
        return int(mask | (main_enum_value << bitshift_amount))
