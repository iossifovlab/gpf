from __future__ import unicode_literals
from builtins import object
import unittest
from variant_annotation.mutation import Mutation, MutatedGenomicSequence
import pytest


class GenomicSequenceMock(object):
    GENOME = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

    def getSequence(self, chromosome, pos_start, pos_end):
        return self.GENOME[pos_start - 1:pos_end]


@pytest.fixture(scope="class")
def genome_seq(request):
    request.cls.genome_seq = GenomicSequenceMock()


@pytest.mark.usefixtures("genome_seq")
class SubstitionMutationTest(unittest.TestCase):
    def test_mutation_full_inside_overlap(self):
        mutation = Mutation(3, "CD", "TT")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 2, 5)
        self.assertEqual("BTTE", result)

    def test_mutation_partial_overlap_before(self):
        mutation = Mutation(3, "CD", "TT")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 4, 7)
        self.assertEqual("TEFG", result)

    def test_mutation_partial_overlap_after(self):
        mutation = Mutation(3, "CD", "TT")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 2, 3)
        self.assertEqual("BT", result)

    def test_mutation_no_overlap_just_before(self):
        mutation = Mutation(3, "CD", "TT")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 5, 7)
        self.assertEqual("EFG", result)

    def test_mutation_no_overlap_just_after(self):
        mutation = Mutation(4, "DE", "TT")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 2, 3)
        self.assertEqual("BC", result)

    def test_mutation_no_overlap_before(self):
        mutation = Mutation(4, "DE", "TT")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 27, 29)
        self.assertEqual("abc", result)

    def test_mutation_no_overlap_after(self):
        mutation = Mutation(31, "DEFGHIJKLMNO", "defghijklmno")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 7, 9)
        self.assertEqual("GHI", result)

    def test_mutation_full_overlap(self):
        mutation = Mutation(4, "DEFGHIJKLMNO", "defghijklmno")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 7, 9)
        self.assertEqual("ghi", result)

    def test_mutation_full_first_overlap(self):
        mutation = Mutation(4, "DEFGHIJKLMNO", "defghijklmno")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 3, 4)
        self.assertEqual("Cd", result)

    def test_mutation_full_last_overlap(self):
        mutation = Mutation(4, "DEFGHIJKLMNO", "defghijklmno")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 15, 16)
        self.assertEqual("oP", result)

    def test_mutation_full_just_before(self):
        mutation = Mutation(4, "DEFGHIJKLMNO", "defghijklmno")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 2, 3)
        self.assertEqual("BC", result)

    def test_mutation_full_just_after(self):
        mutation = Mutation(4, "DEFGHIJKLMNO", "defghijklmno")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 16, 17)
        self.assertEqual("PQ", result)


@pytest.mark.usefixtures("genome_seq")
class InsertionMutationTest(unittest.TestCase):
    def test_mutation_full_inside_overlap(self):
        mutation = Mutation(3, "", "TT")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 2, 5)
        self.assertEqual("BTTC", result)

    def test_mutation_partial_overlap_before(self):
        mutation = Mutation(3, "", "TT")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 4, 7)
        self.assertEqual("TCDE", result)

    def test_mutation_partial_overlap_after(self):
        mutation = Mutation(3, "", "TT")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 2, 3)
        self.assertEqual("BT", result)

    def test_mutation_no_overlap_just_before(self):
        mutation = Mutation(3, "", "TT")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 5, 7)
        self.assertEqual("CDE", result)

    def test_mutation_no_overlap_just_after(self):
        mutation = Mutation(4, "", "TT")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 2, 3)
        self.assertEqual("BC", result)

    def test_mutation_no_overlap_before(self):
        mutation = Mutation(4, "", "TT")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 27, 29)
        self.assertEqual("YZa", result)

    def test_mutation_no_overlap_after(self):
        mutation = Mutation(31, "", "defghijklmno")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 7, 9)
        self.assertEqual("GHI", result)

    def test_mutation_full_overlap(self):
        mutation = Mutation(4, "", "defghijklmno")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 7, 9)
        self.assertEqual("ghi", result)

    def test_mutation_full_last_overlap(self):
        mutation = Mutation(4, "", "defghijklmno")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 15, 16)
        self.assertEqual("oD", result)

    def test_mutation_full_just_before(self):
        mutation = Mutation(4, "", "defghijklmno")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 2, 3)
        self.assertEqual("BC", result)

    def test_mutation_full_just_after(self):
        mutation = Mutation(4, "", "defghijklmno")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 16, 17)
        self.assertEqual("DE", result)


@pytest.mark.usefixtures("genome_seq")
class DeletionMutationTest(unittest.TestCase):
    def test_mutation_full_inside_overlap(self):
        mutation = Mutation(3, "CD", "")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 2, 5)
        self.assertEqual("BEFG", result)

    def test_mutation_partial_overlap_before(self):
        mutation = Mutation(3, "CD", "")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 4, 7)
        self.assertEqual("FGHI", result)

    def test_mutation_partial_overlap_after(self):
        mutation = Mutation(3, "CD", "")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 2, 3)
        self.assertEqual("BE", result)

    def test_mutation_no_overlap_just_before(self):
        mutation = Mutation(3, "CD", "")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 5, 7)
        self.assertEqual("GHI", result)

    def test_mutation_no_overlap_just_after(self):
        mutation = Mutation(4, "DE", "")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 2, 3)
        self.assertEqual("BC", result)

    def test_mutation_no_overlap_before(self):
        mutation = Mutation(4, "DE", "")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 27, 29)
        self.assertEqual("cde", result)

    def test_mutation_no_overlap_after(self):
        mutation = Mutation(31, "defghijklmno", "")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 7, 9)
        self.assertEqual("GHI", result)

    def test_mutation_full_overlap(self):
        mutation = Mutation(4, "DEFGHIJKLMNOP", "")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 7, 9)
        self.assertEqual("TUV", result)

    def test_mutation_full_last_overlap(self):
        mutation = Mutation(4, "DEFGHIJKLMNOP", "")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 3, 4)
        self.assertEqual("CQ", result)

    def test_mutation_full_just_before(self):
        mutation = Mutation(4, "DEFGHIJKLMNOP", "")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 2, 3)
        self.assertEqual("BC", result)

    def test_mutation_full_just_after(self):
        mutation = Mutation(4, "DEFGHIJKLMNOP", "")
        seq = MutatedGenomicSequence(self.genome_seq, mutation)
        result = seq.get_sequence("1", 16, 17)
        self.assertEqual("cd", result)


if __name__ == "__main__":
    unittest.main()
