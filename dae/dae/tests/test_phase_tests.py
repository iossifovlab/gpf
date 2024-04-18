# pylint: disable=W0621,C0114,C0116,W0212,W0613,missing-class-docstring
import unittest

import numpy as np

from dae.tools.phase import checkConsistency, getDims, phase


class PhaseTest(unittest.TestCase):
    # pylint: disable=invalid-name

    inpR = [
        [[1, 2, 2, 1], [1, 0, 0, 1]],
        [[1, 2, 1, 2], [1, 0, 1, 0]],
    ]
    inp = [np.array(x) for x in inpR]
    inp_fail_loci = [
        np.array([[1, 2, 2, 1], [1, 0, 0, 1]]),
        np.array([[1, 2, 2, 1], [1, 0, 1, 1]]),
    ]

    def test_dims_length(self):
        L, _P, _nCpies = getDims(self.inp)
        self.assertEqual(2, L)

    def test_dims_p(self):
        _L, P, _nCpies = getDims(self.inp)
        self.assertEqual(4, P)

    def test_dims_copies(self):
        _L, _P, nCpies = getDims(self.inp)
        self.assertTrue(np.array_equal(np.array([2, 2, 2, 2]), nCpies))

    def test_consistence(self):
        self.assertTrue(checkConsistency(self.inp))

    def test_consistence_fail_loci(self):
        self.assertRaises(Exception, checkConsistency, self.inp_fail_loci)

    def test_phase(self):
        res = phase(self.inp)
        print(res)
        for r in res:
            print("r:", r)
            print("mom:", r[0])
            print("dad:", r[1])

        # self.asertEqual(res)
