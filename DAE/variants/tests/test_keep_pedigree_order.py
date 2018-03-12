'''
Created on Mar 12, 2018

@author: lubo
'''
from __future__ import print_function

from RegionOperations import Region
from variants.vcf_utils import mat2str, VcfFamily
from variants.family import FamiliesBase
from variants.loader import RawVariantsLoader
import StringIO
from variants.attributes import Role


'''
2235 1:908193(908193) sub(T->G) SF0043014 212/010 000/010 intron PLEKHN1:intron denovo 0 0.0
2236 1:908193(908193) sub(T->G) SF0033119 212/010 000/010 intron PLEKHN1:intron denovo 0 0.0
2237 1:908193(908193) sub(T->G) SF0014912 122/100 000/100 intron PLEKHN1:intron denovo 0 0.0
2238 1:908193(908193) sub(T->G) SF0042658 212/010 000/010 intron PLEKHN1:intron denovo 0 0.0
'''


def test_denovo_order_experiment(nvcf19):
    regions = [
        Region("1", 908193, 908193),
    ]

    vs = nvcf19.query_variants(
        regions=regions,
        inheritance='denovo')
    for v in vs:
        print(v, v.family_id, mat2str(v.best_st), mat2str(v.gt),
              v.effect_type, v.effect_gene, v.inheritance,
              v.get_attr('all.nAltAlls'), v.get_attr('all.altFreq'))
        print(v.members_in_order)
        print(v.members_ids)
        assert v.members_in_order[-1].role == Role.prb


# def test_pedigree_sorted(nvcf19_config):
#     ped_df = RawVariantsLoader.load_pedigree_file(nvcf19_config.pedigree)
#     ped_df = RawVariantsLoader.sort_pedigree(ped_df)
#     RawVariantsLoader.save_pedigree_file(ped_df, "ped.ped")


PED_FILE1 = """
familyId,personId,dadId,momId,sex,status,role
SF0043014,SP0041907,0,0,2,1,mom
SF0043014,SP0043015,0,0,1,1,dad
SF0043014,SP0043014,SP0043015,SP0041907,1,2,prb
SF0033119,SP0033118,0,0,2,1,mom
SF0033119,SP0033120,0,0,1,1,dad
SF0033119,SP0033119,SP0033120,SP0033118,1,2,prb
SF0014912,SP0015221,0,0,2,1,mom
SF0014912,SP0024751,0,0,1,1,dad
SF0014912,SP0014912,SP0024751,SP0015221,1,2,prb
"""


def test_pedigree_keep_family_order_local():
    ped_df = RawVariantsLoader.load_pedigree_file(
        StringIO.StringIO(PED_FILE1), sep=",")
    families = FamiliesBase(ped_df)
    families.families_build(ped_df, family_class=VcfFamily)

    f = families.families['SF0043014']
    print(f.members_in_order)
    assert f.members_in_order[-1].role == Role.prb
    f = families.families['SF0033119']
    print(f.members_in_order)
    assert f.members_in_order[-1].role == Role.prb
    f = families.families['SF0014912']
    print(f.members_in_order)
    assert f.members_in_order[-1].role == Role.prb


def test_pedigree_keep_family_order(nvcf19):
    families = nvcf19

    f = families.families['SF0043014']
    print(f.members_in_order)
    assert f.members_in_order[-1].role == Role.prb
    f = families.families['SF0033119']
    print(f.members_in_order)
    assert f.members_in_order[-1].role == Role.prb
    f = families.families['SF0014912']
    print(f.members_in_order)
    assert f.members_in_order[-1].role == Role.prb
    f = families.families['SF0042658']
    print(f.members_in_order)
    assert f.members_in_order[-1].role == Role.prb
