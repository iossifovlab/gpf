import pytest


test_data = [(str(chrom), 123123, False) for chrom in range(1, 23)]
test_data.append(("X", 1, False))
test_data.append(("X", 60001, True))
test_data.append(("X", 100000, True))
test_data.append(("X", 2700000, False))
test_data.append(("X", 154931044, True))
test_data.append(("X", 154931050, True))
test_data.append(("X", 155260560, True))
test_data.append(("X", 155260600, False))
test_data.append(("Y", 1, False))
test_data.append(("Y", 10001, True))
test_data.append(("Y", 100000, True))
test_data.append(("Y", 2700000, False))
test_data.append(("Y", 59034050, True))
test_data.append(("Y", 59035000, True))
test_data.append(("Y", 59363566, True))
test_data.append(("Y", 59363600, False))

# test_data_chr_prefix = list(
#     map(lambda x: ("chr" + x[0], x[1], x[2]), test_data)
# )
# test_data.extend(test_data_chr_prefix)


@pytest.mark.parametrize("chrom,pos,expected", [*test_data])
def test_is_pseudoautosomal(chrom, pos, expected, genome_2013):
    genomic_sequence = genome_2013.get_genomic_sequence()
    assert genomic_sequence.is_pseudoautosomal(chrom, pos) == expected
