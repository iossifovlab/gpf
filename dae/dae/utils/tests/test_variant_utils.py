import pytest

from typing import List, Union

from dae.utils.variant_utils import get_locus_ploidy, reverse_complement
from dae.variants.attributes import Sex

chroms: List[Union[int, str]] = list(range(1, 23))
chroms.append("Y")

test_data = [
    (str(chrom), 123123, sex, 2)
    for sex in (Sex.M, Sex.F)
    for chrom in list(range(1, 23))
]
test_data.append(("X", 1, Sex.F, 2))
test_data.append(("X", 60001, Sex.F, 2))
test_data.append(("X", 100000, Sex.F, 2))
test_data.append(("X", 2700000, Sex.F, 2))
test_data.append(("X", 154931044, Sex.F, 2))
test_data.append(("X", 154931050, Sex.F, 2))
test_data.append(("X", 155260560, Sex.F, 2))
test_data.append(("X", 155260600, Sex.F, 2))
test_data.append(("X", 1, Sex.M, 1))
test_data.append(("X", 60001, Sex.M, 2))
test_data.append(("X", 100000, Sex.M, 2))
test_data.append(("X", 2700000, Sex.M, 1))
test_data.append(("X", 154931044, Sex.M, 2))
test_data.append(("X", 154931050, Sex.M, 2))
test_data.append(("X", 155260560, Sex.M, 2))
test_data.append(("X", 155260600, Sex.M, 1))

# test_data_chr_prefix = list(
#     map(lambda x: ("chr" + x[0], x[1], x[2], x[3]), test_data)
# )
# test_data.extend(test_data_chr_prefix)


@pytest.mark.parametrize("chrom,pos,sex,expected", [*test_data])
def test_get_locus_ploidy(chrom, pos, sex, expected, genome_2013):
    assert get_locus_ploidy(chrom, pos, sex, genome_2013) == expected


@pytest.mark.parametrize("dna,expected", [
    ("a", "T"),
    ("ac", "GT"),
    ("actg", "CAGT"),
])
def test_reverse_complement(dna, expected):
    result = reverse_complement(dna)
    assert result == expected
