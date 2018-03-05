'''
Created on Mar 5, 2018

@author: lubo
'''
from __future__ import print_function

from variants.raw_vcf import AlleleCounter


def test_allele_counter_simple(ustudy):

    counter = AlleleCounter(ustudy)
    assert counter is not None

    persons = ustudy.persons_without_parents()
    print(persons)

    assert persons
    persons_index = ustudy.persons_index(persons)
    print(persons_index)

    assert persons_index


def test_allels_counter_simple_vcf(ustudy):
    counter = AlleleCounter(ustudy)

    for v in ustudy.vcf_vars:
        res = counter.count_alt_allele(v)
        print(res)
