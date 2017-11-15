from tools.vcf2DAEc import getGT, getVrtFam
from itertools import izip_longest


class DataMock():
    def __init__(self, gt, alts):
        self.samples = dict()
        self.samples['1'] = dict()
        self.samples['1']['GT'] = gt

        self.alts = alts


def test_getGT_ref():
    data = DataMock([0, 0], ['A'])
    fx, gt, cx = getGT('1', data)
    assert(fx)
    assert(all(a == b for a, b in izip_longest(gt, [2, 0])))
    assert(all(a == b for a, b in izip_longest(cx, [-1, -1])))


def test_getGT_two_in_first_alt():
    data = DataMock([1, 1], ['A'])
    fx, gt, cx = getGT('1', data)
    assert(fx)
    assert(all(a == b for a, b in izip_longest(gt, [0, 2])))
    assert(all(a == b for a, b in izip_longest(cx, [-1, -1])))


def test_getGT_one_in_first_alt():
    data = DataMock([0, 1], ['A'])
    fx, gt, cx = getGT('1', data)
    assert(fx)
    assert(all(a == b for a, b in izip_longest(gt, [1, 1])))
    assert(all(a == b for a, b in izip_longest(cx, [-1, -1])))


def test_getGT_one_in_second_alt():
    data = DataMock([0, 2], ['A', 'T'])
    fx, gt, cx = getGT('1', data)
    assert(fx)
    assert(all(a == b for a, b in izip_longest(gt, [1, 0, 1])))
    assert(all(a == b for a, b in izip_longest(cx, [-1, -1, -1])))


def test_getGT_one_in_complimentary_second_alt():
    data = DataMock([2, 0], ['A', 'T'])
    fx, gt, cx = getGT('1', data)
    assert(fx)
    assert(all(a == b for a, b in izip_longest(gt, [1, 0, 1])))
    assert(all(a == b for a, b in izip_longest(cx, [-1, -1, -1])))


def test_getGT_two_in_second_alt():
    data = DataMock([2, 2], ['A', 'T'])
    fx, gt, cx = getGT('1', data)
    assert(fx)
    assert(all(a == b for a, b in izip_longest(gt, [0, 0, 2])))
    assert(all(a == b for a, b in izip_longest(cx, [-1, -1, -1])))


def test_getGT_one_per_each_alt():
    data = DataMock([2, 1], ['A', 'T'])
    fx, gt, cx = getGT('1', data)
    assert(fx)
    assert(all(a == b for a, b in izip_longest(gt, [0, 1, 1])))
    assert(all(a == b for a, b in izip_longest(cx, [-1, -1, -1])))


def test_getVrtFam():
    data = DataMock([2, 1], ['A', 'T'])
    fx, gt, cx = getVrtFam(['1'], data)
    print(fx, gt, cx)
    assert(fx)
    assert(len(gt) == 1)
    assert(len(cx) == 1)
    assert(all(a == b for a, b in izip_longest(gt[0], [0, 1, 1])))
    assert(all(a == b for a, b in izip_longest(cx[0], [-1, -1, -1])))
