# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap
from enum import Enum

import numpy as np
import pytest
from gain.genomic_resources.reference_genome import (
    ReferenceGenome,
    build_reference_genome_from_resource,
)
from gain.genomic_resources.repository import GR_CONF_FILE_NAME
from gain.genomic_resources.testing import (
    build_filesystem_test_resource,
    setup_directories,
)
from gpf.utils.variant_utils import (
    BitmaskEnumTranslator,
    get_locus_ploidy,
    gt2str,
    str2gt,
)
from gpf.variants.attributes import Role, Sex, Status, Zygosity


@pytest.fixture
def genome(tmp_path: pathlib.Path) -> ReferenceGenome:
    root_path = tmp_path
    setup_directories(root_path, {
        GR_CONF_FILE_NAME: """
            type: genome
            filename: chr.fa
            PARS:
                X:
                    - "X:10000-2781479"
                    - "X:155701382-156030895"
                Y:
                    - "Y:10000-2781479"
                    - "Y:56887902-57217415"
        """,
        "chr.fa": textwrap.dedent("""
            >pesho
            NGNACCCAAAC
            GGGCCTTCCN
            NNNA
            >gosho
            NNAACCGGTT
            TTGCCAANN"""),
        "chr.fa.fai": "pesho\t24\t8\t10\t11\ngosho\t20\t42\t10\t11",
    })
    res = build_filesystem_test_resource(root_path)
    return build_reference_genome_from_resource(res)


chroms: list[int | str] = list(range(1, 23))
chroms.append("Y")

test_data = [
    (str(chrom), 50, sex, 2)
    for sex in (Sex.M, Sex.F)
    for chrom in list(range(1, 23))
]

test_data.extend(
    (
        ("X", 500, Sex.M, 1),
        ("X", 10000, Sex.M, 2),
        ("X", 105000, Sex.M, 2),
        ("X", 2781479, Sex.M, 2),
        ("X", 3000000, Sex.M, 1),
        ("X", 155700000, Sex.M, 1),
        ("X", 155701382, Sex.M, 2),
        ("X", 156000000, Sex.M, 2),
        ("X", 156030895, Sex.M, 2),
        ("X", 200000000, Sex.M, 1),
        ("Y", 500, Sex.M, 1),
        ("Y", 10000, Sex.M, 2),
        ("Y", 105000, Sex.M, 2),
        ("Y", 2781479, Sex.M, 2),
        ("Y", 3000000, Sex.M, 1),
        ("Y", 56800000, Sex.M, 1),
        ("Y", 56887902, Sex.M, 2),
        ("Y", 56900000, Sex.M, 2),
        ("Y", 57000000, Sex.M, 2),
        ("Y", 57217415, Sex.M, 2),
        ("Y", 60000000, Sex.M, 1),
        ("X", 500, Sex.U, 1),
        ("X", 10000, Sex.U, 2),
        ("X", 105000, Sex.U, 2),
        ("X", 2781479, Sex.U, 2),
        ("X", 3000000, Sex.U, 1),
        ("X", 155700000, Sex.U, 1),
        ("X", 155701382, Sex.U, 2),
        ("X", 156000000, Sex.U, 2),
        ("X", 156030895, Sex.U, 2),
        ("X", 200000000, Sex.U, 1),
        ("Y", 500, Sex.U, 1),
        ("Y", 10000, Sex.U, 2),
        ("Y", 105000, Sex.U, 2),
        ("Y", 2781479, Sex.U, 2),
        ("Y", 3000000, Sex.U, 1),
        ("Y", 56800000, Sex.U, 1),
        ("Y", 56887902, Sex.U, 2),
        ("Y", 56900000, Sex.U, 2),
        ("Y", 57000000, Sex.U, 2),
        ("Y", 57217415, Sex.U, 2),
        ("Y", 60000000, Sex.U, 1),
        ("X", 500, Sex.F, 2),
        ("X", 155701382, Sex.F, 2),
        ("X", 2781479, Sex.F, 2),
        ("X", 156030895, Sex.F, 2),
        ("X", 57217415, Sex.F, 2),
    ),
)


@pytest.mark.parametrize("chrom,pos,sex,expected", [*test_data])
def test_get_locus_ploidy(
    genome: ReferenceGenome,
    chrom: str,
    pos: int,
    sex: Sex,
    expected: int,
) -> None:
    assert get_locus_ploidy(chrom, pos, sex, genome) == expected


def test_get_locus_ploidy_y_chrom_female(genome: ReferenceGenome) -> None:
    assert get_locus_ploidy("Y", 57217415, Sex.F, genome) == 0


@pytest.mark.parametrize("gt,expected", [
    (
        np.array([[0, 0, 0], [0, 1, 0]], dtype=np.int8),
        "0/0,0/1,0/0",
    ),
    (
        np.array([[0, 0, 0], [0, -1, 0]], dtype=np.int8),
        "0/0,0/.,0/0",
    ),
    (
        np.array([[0, 1, 0], [0, -1, 0]], dtype=np.int8),
        "0/0,1/.,0/0",
    ),
])
def test_gt2str(gt: np.ndarray, expected: np.ndarray) -> None:
    res = gt2str(gt)

    assert res == expected


@pytest.mark.parametrize("gts,expected", [
    (
        "0/0,0/1,0/0",
        np.array([[0, 0, 0], [0, 1, 0]], dtype=np.int8),
    ),
    (
        "0/0,0/.,0/0",
        np.array([[0, 0, 0], [0, -1, 0]], dtype=np.int8),
    ),
    (
        "0/0,1/.,0/0",
        np.array([[0, 1, 0], [0, -1, 0]], dtype=np.int8),
    ),
])
def test_str2gt(gts: str, expected: np.ndarray) -> None:
    res = str2gt(gts)

    assert np.all(res == expected)


@pytest.mark.parametrize(
    "main_enum,partition_by_enum,value,partition_value,expected",
    [
        (
            Zygosity, Status,
            Zygosity.homozygous, Status.unaffected, 1 << (0 * 2),
        ),
        (
            Zygosity, Status,
            Zygosity.heterozygous, Status.unaffected, 2 << (0 * 2),
        ),
        (
            Zygosity, Status,
            Zygosity.homozygous, Status.affected, 1 << (1 * 2),
        ),
        (
            Zygosity, Status,
            Zygosity.heterozygous, Status.affected, 2 << (1 * 2),
        ),
        (
            Zygosity, Role,
            Zygosity.homozygous, Role.maternal_grandmother, 1 << (0 * 2),
        ),
        (
            Zygosity, Role,
            Zygosity.homozygous, Role.maternal_grandfather, 1 << (1 * 2),
        ),
        (
            Zygosity, Role,
            Zygosity.homozygous, Role.paternal_grandmother, 1 << (2 * 2),
        ),
        (
            Zygosity, Role,
            Zygosity.homozygous, Role.paternal_grandfather, 1 << (3 * 2),
        ),
        (
            Zygosity, Role,
            Zygosity.homozygous, Role.mom, 1 << (4 * 2),
        ),
        (
            Zygosity, Role,
            Zygosity.homozygous, Role.dad, 1 << (5 * 2),
        ),
        (
            Zygosity, Role,
            Zygosity.heterozygous, Role.dad, 2 << (5 * 2),
        ),
        (
            Zygosity, Role,
            Zygosity.homozygous, Role.parent, 1 << (6 * 2),
        ),
        (
            Zygosity, Role,
            Zygosity.homozygous, Role.half_sibling, 1 << (12 * 2),
        ),
        (
            Zygosity, Role,
            Zygosity.homozygous, Role.maternal_aunt, 1 << (16 * 2),
        ),
        (
            Zygosity, Role,
            Zygosity.homozygous, Role.spouse, 1 << (24 * 2),
        ),
        (
            Zygosity, Role,
            Zygosity.homozygous, Role.unknown, 1 << (25 * 2),
        ),
    ],
)
def test_bitmask_translator(
        main_enum: type[Enum], partition_by_enum: type[Enum],
        value: Enum, partition_value: Enum, expected: int,
) -> None:
    translator = BitmaskEnumTranslator(
        main_enum_type=main_enum, partition_by_enum_type=partition_by_enum)

    assert translator.apply_mask(0, value.value, partition_value) == expected
