from __future__ import unicode_literals
from builtins import range
from builtins import object
import re


class Variant(object):
    def __init__(self, chrom=None, position=None, loc=None, var=None, ref=None,
                 alt=None, length=None, seq=None, typ=None):
        self.set_position(chrom, position, loc)
        self.set_ref_alt(var, ref, alt, length, seq, typ)

        self.ref_position_last = self.position + len(self.reference)
        self.alt_position_last = self.position + len(self.alternate)

        self.corrected_ref_position_last = max(self.position,
                                               self.ref_position_last - 1)

    def set_position(self, chromosome, position, loc):
        if position is not None:
            assert(chromosome is not None)
            assert(loc is None)
            self.chromosome = chromosome
            self.position = int(position)

        if loc is not None:
            assert(chromosome is None)
            assert(position is None)
            loc_arr = loc.split(":")
            self.chromosome = loc_arr[0]
            self.position = int(loc_arr[1])

        assert(self.chromosome is not None)
        assert(self.position is not None)

    def set_ref_alt(self, var, ref, alt, length, seq, typ):
        if ref is not None:
            assert(alt is not None)
            assert(var is None)
            assert(length is None)
            assert(seq is None)
            assert(typ is None)
            self.reference = ref
            self.alternate = alt

        if var is not None:
            assert(ref is None)
            assert(alt is None)
            assert(length is None)
            assert(seq is None)
            assert(typ is None)
            self.set_ref_alt_from_variant(var)

        self.trim_equal_ref_alt_parts()
        assert(self.reference is not None)
        assert(self.alternate is not None)

    def trim_equal_ref_alt_parts(self):
        start_index = -1
        for i in range(min(len(self.reference), len(self.alternate))):
            if self.reference[i] == self.alternate[i]:
                start_index = i
            else:
                break

        self.reference = self.reference[start_index + 1:]
        self.alternate = self.alternate[start_index + 1:]
        self.position += start_index + 1

    def set_ref_alt_from_variant(self, var):
        if var.startswith("complex"):
            a = re.match('.*\\((.*)->(.*)\\)', var)
            self.reference = a.group(1).upper()
            self.alternate = a.group(2).upper()
            return

        t = var[0].upper()
        if t == "S":
            a = re.match('.*\\((.*)->(.*)\\)', var)
            self.reference = a.group(1).upper()
            self.alternate = a.group(2).upper()
            return

        if t == "D":
            a = re.match('.*\\((.*)\\)', var)
            self.reference = "0" * int(a.group(1))
            self.alternate = ""
            return

        if t == "I":
            a = re.match('.*\\((.*)\\)', var)
            self.reference = ""
            self.alternate = re.sub('[0-9]+', '', a.group(1).upper())
            return

        raise Exception("Unknown variant!: " + var)
