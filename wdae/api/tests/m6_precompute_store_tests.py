'''
Created on Jun 11, 2015

@author: lubo
'''
from django.test import TestCase

class Test(TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def test_store_retrieve_simple(self):
        from api.precompute import cache
        store = cache.PrecomputeStore()
        
        data = {"a": "1", "b": "ala-bala"}
        store.store("my_data", data)

        data1 = store.retrieve("my_data")
        print data1
        
        self.assertEquals(data, data1)
        
