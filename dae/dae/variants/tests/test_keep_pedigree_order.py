from io import StringIO

from dae.pedigrees.loader import FamiliesLoader
from dae.variants.attributes import Role


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

"""
2235 1:908193(908193) sub(T->G) SF0043014 212/010 000/010 denovo 0 0.0
2236 1:908193(908193) sub(T->G) SF0033119 212/010 000/010 denovo 0 0.0
2237 1:908193(908193) sub(T->G) SF0014912 122/100 000/100 denovo 0 0.0
2238 1:908193(908193) sub(T->G) SF0042658 212/010 000/010 denovo 0 0.0
"""


def test_pedigree_keep_family_order_local():
    loader = FamiliesLoader(StringIO(PED_FILE1), ped_sep=",")
    families = loader.load()

    f = families["SF0043014"]
    print(f.members_in_order)
    assert f.members_in_order[-1].role == Role.prb
    f = families["SF0033119"]
    print(f.members_in_order)
    assert f.members_in_order[-1].role == Role.prb
    f = families["SF0014912"]
    print(f.members_in_order)
    assert f.members_in_order[-1].role == Role.prb
