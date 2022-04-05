import re

SUB_COMPLEX_RE = re.compile(r"^(sub|complex|comp)\(([NACGT]+)->([NACGT]+)\)$")
INS_RE = re.compile(r"^ins\(([NACGT]+)\)$")
DEL_RE = re.compile(r"^del\((\d+)\)$")


def cached(prop):
    cached_val_name = "_" + prop.__name__

    def wrap(self):
        if getattr(self, cached_val_name, None) is None:
            setattr(self, cached_val_name, prop(self))
        return getattr(self, cached_val_name)
    return wrap


def dae2vcf_variant(chrom, position, var, genome):
    match = SUB_COMPLEX_RE.match(var)
    if match:
        return position, match.group(2), match.group(3)

    match = INS_RE.match(var)
    if match:
        alt_suffix = match.group(1)
        reference = genome.get_sequence(chrom, position - 1, position - 1)
        return position - 1, reference, reference + alt_suffix

    match = DEL_RE.match(var)
    if match:
        count = int(match.group(1))
        reference = genome.get_sequence(
            chrom, position - 1, position + count - 1
        )
        assert len(reference) == count + 1, reference
        return position - 1, reference, reference[0]

    raise NotImplementedError("weird variant: " + var)


def split_iterable(iterable, max_chunk_length=50):
    i = 0
    result = []

    for value in iterable:
        i += 1
        result.append(value)

        if i == max_chunk_length:
            yield result
            result = []
            i = 0

    if i != 0:
        yield result


def join_line(ln, sep="\t"):
    lm = map(lambda v: "; ".join(v) if isinstance(v, list) else v, ln)
    tl = map(lambda v: "" if v is None or v == "None" else str(v), lm)
    return sep.join(tl) + "\n"
