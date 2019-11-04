'''
Created on Mar 12, 2018

@author: lubo
'''
from io import StringIO

from dae.pedigrees.pedigree_reader import PedigreeReader
from dae.variants.attributes import Role
from dae.variants.family import FamiliesBase, Family


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

'''
2235 1:908193(908193) sub(T->G) SF0043014 212/010 000/010 denovo 0 0.0
2236 1:908193(908193) sub(T->G) SF0033119 212/010 000/010 denovo 0 0.0
2237 1:908193(908193) sub(T->G) SF0014912 122/100 000/100 denovo 0 0.0
2238 1:908193(908193) sub(T->G) SF0042658 212/010 000/010 denovo 0 0.0
'''


def test_pedigree_keep_family_order_local():
    ped_df = PedigreeReader.load_pedigree_file(
        StringIO(PED_FILE1), sep=",")
    families = FamiliesBase(ped_df)
    families.families_build(ped_df, family_class=Family)

    f = families.families['SF0043014']
    print(f.members_in_order)
    assert f.members_in_order[-1].role == Role.prb
    f = families.families['SF0033119']
    print(f.members_in_order)
    assert f.members_in_order[-1].role == Role.prb
    f = families.families['SF0014912']
    print(f.members_in_order)
    assert f.members_in_order[-1].role == Role.prb
