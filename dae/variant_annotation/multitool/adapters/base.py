from variant_annotation.variant import Variant


class BaseAdapter(object):
    def annotate_variant(self, chr=None, position=None, loc=None, var=None,
                         ref=None, alt=None, length=None, seq=None,
                         typ=None):
        variant = Variant(chr, position, loc, var, ref, alt, length, seq, typ)
        return self.annotate(variant)
