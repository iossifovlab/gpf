'''
Created on Aug 23, 2016

@author: lubo
'''
from pheno_db.precompute.individuals import Individuals
from DAE import vDB


def test_individuals_load():
    individuals = Individuals()
    individuals.load()

    assert individuals.families is not None


def test_check_individuals_in_ssc_dataset():
    individuals = Individuals()
    individuals.load()
    families = individuals.families

    studies = vDB.get_studies('ALL SSC')
    for st in studies:
        for fid, stfam in st.families.items():
            if fid not in families:
                print("\nfid: {} from study: {} not found in PhenoDB\n".format(
                    fid, st.name))
                continue

            fam = families[fid]

            for stp in stfam.memberInOrder:
                check = [p.personId == stp.personId for p in fam.memberInOrder]
                if not any(check):
                    print("fid: {} from study: {} bad members: \n"
                          "\tpheno: {}\n"
                          "\tstudy: {}\n"
                          .format(
                              fid, st.name,
                              stfam.memberInOrder, fam.memberInOrder))
                # assert any(check)
