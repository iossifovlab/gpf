'''
Created on Dec 10, 2015

@author: lubo
'''
import unittest
from preloaded import register


class Test(unittest.TestCase):

    def test_gene_weights_preload(self):
        weights = register.get('gene_weights')
        self.assertIsNotNone(weights)


if __name__ == "__main__":
    unittest.main()
