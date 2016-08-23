'''
Created on Aug 23, 2016

@author: lubo
'''
from DAE import vDB
from pheno_db.precompute.individuals import Individuals


def test_individuals_load():
    individuals = Individuals()
    individuals.load()

    assert individuals.families is not None


def get_all_ssc_studies():
    study_group = vDB.get_study_group('ALL SSC')
    denovo_studies = study_group.get_attr('studies')
    transmitted_studies = study_group.get_attr('transmittedStudies')
    studies = []
    studies.extend(vDB.get_studies(denovo_studies))
    studies.extend(vDB.get_studies(transmitted_studies))
    return studies


def test_check_individuals_in_ssc_dataset():
    individuals = Individuals()
    individuals.load()
    families = individuals.families

    studies = get_all_ssc_studies()

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


def test_phenodb_individuals_are_in_ssc_dataset():
    individuals = Individuals()
    individuals.load()
    families = individuals.families
    df = individuals.df

    assert df is not None
    assert families is not None

    persons = {}
    for _index, val in df.personId.iteritems():
        persons[val] = []

    for st in get_all_ssc_studies():
        print("checking study: {}".format(st.name))
        for _fid, fam in st.families.items():
            for p in fam.memberInOrder:
                if p.personId not in persons:
                    print("person: {} from study: {} not found in PhenoDB"
                          .format(p.personId, st.name))
                    continue
                persons[p.personId].append((st.name, p))

    missing = []
    for pid, studies in persons.items():
        if len(studies) == 0:
            missing.append(pid)

    missing.sort()
    print("persons from PhenoDB missing in SSC ALL: {}".format(missing))
