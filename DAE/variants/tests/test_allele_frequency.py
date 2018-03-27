'''
Created on Mar 5, 2018

@author: lubo
'''
from __future__ import print_function
from variants.annotate_allele_frequencies import VcfAlleleFrequencyAnnotator


def test_allele_counter_simple(ustudy_single):

    counter = VcfAlleleFrequencyAnnotator()
    counter.setup(ustudy_single)

    assert counter is not None

    persons = ustudy_single.persons_without_parents()
    print(persons)

    assert persons
    persons_index = ustudy_single.persons_index(persons)
    print(persons_index)

    assert persons_index


def test_allels_counter_simple_vcf(ustudy_single):
    counter = VcfAlleleFrequencyAnnotator()
    counter.setup(ustudy_single)

    for v in ustudy_single.vcf_vars:
        res = counter.annotate_variant(v)
        # print(res)
        assert res is not None
