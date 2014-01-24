import numpy as np
import unittest

from phase import phase, getDims, checkConsistency


class PhaseTest(unittest.TestCase):

    inpR = [
        [[1, 2, 2, 1],
         [1, 0, 0, 1]],
        [[1, 2, 1, 2],
         [1, 0, 1, 0]],
    ]
    inp = [np.array(x) for x in inpR]
    inp_fail_shape = [np.array([[1, 2, 2, 1], [1, 0, 0]])]
    inp_fail_loci = [np.array([[1, 2, 2, 1], [1, 0, 0, 1]]),
                     np.array([[1, 2, 2, 1], [1, 0, 1, 1]])]

    def test_dims_length(self):
        L, P, nCpies = getDims(self.inp)
        self.assertEqual(2, L)

    def test_dims_p(self):
        L, P, nCpies = getDims(self.inp)
        self.assertEqual(4, P)

    def test_dims_copies(self):
        L, P, nCpies = getDims(self.inp)
        self.assertTrue(np.array_equal(np.array([2, 2, 2, 2]), nCpies))

    def test_consistence(self):
        self.assertTrue(checkConsistency(self.inp))

    def test_consistence_fail_shape(self):
        self.assertRaises(Exception, checkConsistency, self.inp_fail_shape)

    def test_consistence_fail_loci(self):
        self.assertRaises(Exception, checkConsistency, self.inp_fail_loci)

    # def test_phase(self):
    #     res = phase(self.inp)
    #     print res
    #     for r in res:
    #         print "r:", r
    #         print 'mom:', r[0]
    #         print 'dad:', r[1]

    #     self.asertEqual(res)
