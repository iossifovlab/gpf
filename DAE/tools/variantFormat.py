from __future__ import print_function
from __future__ import unicode_literals

from builtins import zip
from builtins import str
import sys


# is autosomal X for hg19
def isPseudoAutosomalX(pos):
        # hg19 pseudo autosomes region: chrX:60001-2699520
        # and chrX:154931044-155260560 are hg19's pseudo autosomal
        flag = not (
            (pos < 60001) or
            ((pos >= 2699520) and (pos < 154931044)) or
            (pos >= 155260560))

        return flag


def trimStr(pos, ref, alt):
    for n, s in enumerate(zip(ref[::-1], alt[::-1])):
        if s[0] != s[1]:
            break

    # not made simple
    if ref[-(n+1)] == alt[-(n+1)]:
        r, a = ref[:-(n+1)], alt[:-(n+1)]
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
        return pos+n+1, r[n+1:], a[n+1:]

    return pos+n, r[n:], a[n:]


def cshlFormat(pos, ref, alt):
    p, r, a = trimStr(pos, ref, alt)
    if len(r) == len(a) and len(r) == 0:
        print(
            'ref {:s} is the same as alt {:s}'.format(ref, alt),
            file=sys.stderr)
        return p, 'complex(' + r + '->' + a + ')'

    if len(r) == len(a) and len(r) == 1:
        wx = 'sub(' + r + '->' + a + ')'
        return p, wx

    if len(r) > len(a) and len(a) == 0:
        wx = 'del(' + str(len(r)) + ')'
        return p, wx

    # len(ref) < len(alt):
    if len(r) < len(a) and len(r) == 0:
        wx = 'ins(' + a + ')'
        return p, wx

    return p, 'complex(' + r + '->' + a + ')'


def vcf2cshlFormat2(pos, ref, alts):
    vrt, pxx = list(), list()
    for alt in alts:
        p, v = cshlFormat(pos, ref, alt)

        pxx.append(p)
        vrt.append(v)

    return pxx, vrt


def main():
    print("IN: vcf2cshlFormat2( 1, 'A', ['AA','AC','G','GA','AC','ACAAC'] )")
    print(vcf2cshlFormat2(1, 'A', ['AA', 'AC', 'G', 'GA', 'AC', 'ACAAC']))

    print(
        "IN: vcf2cshlFormat2( 1, 'AA', ['AA','AC','AAA','A',"
        "'AC','CA','ACAAC','CAAAAA'] )"
    )
    print(vcf2cshlFormat2(
        1, 'AA', ['AA', 'AC', 'AAA', 'A', 'AC', 'CA', 'ACAAC', 'CAAAAA']))

    print(
        "IN: vcf2cshlFormat2( 1, 'AAAAAA', ['AAAAAC','AAA','A','ACAAAA',"
        "'CAAAAAA','AACAAC','CAAAAA'] )"
    )
    print(vcf2cshlFormat2(
        1, 'AAAAAA',
        ['AAAAAC', 'AAA', 'A', 'ACAAAA', 'CAAAAAA', 'AACAAC', 'CAAAAA']))


if __name__ == "__main__":
    main()
