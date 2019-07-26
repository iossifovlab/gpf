'''
Created on Dec 8, 2016

@author: lubo
'''
from __future__ import unicode_literals


def test_pheno_factory_simple(fake_pheno_factory):
    assert fake_pheno_factory.config is not None


def test_check_pheno_db(fake_pheno_factory):
    assert fake_pheno_factory.has_pheno_db('fake')


def test_get_pheno_db(fake_pheno_factory):
    fphdb = fake_pheno_factory.get_pheno_db('fake')
    assert fphdb is not None
    assert fphdb.families is not None
    assert fphdb.instruments is not None


def test_get_pheno_db_names(fake_pheno_factory):
    dbs = fake_pheno_factory.get_pheno_db_names()
    assert dbs is not None
    assert len(dbs) == 3
