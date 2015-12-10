'''
Created on Dec 10, 2015

@author: lubo
'''
import unittest
from api.preloaded.register import get_register


class Test(unittest.TestCase):

    def test_gene_weights_preload(self):
        register = get_register()
        weights = register.get('gene_weights')
        self.assertIsNotNone(weights)


if __name__ == "__main__":
    unittest.main()
