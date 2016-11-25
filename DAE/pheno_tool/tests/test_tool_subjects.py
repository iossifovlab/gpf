'''
Created on Nov 25, 2016

@author: lubo
'''
from pheno_tool.tool import PhenoTool


def test_pheno_tool_proband_subjects(phdb, all_ssc_studies):
    tool = PhenoTool(phdb, all_ssc_studies, roles=['prb'])
    assert tool is not None

    persons = tool.list_of_subjects()
    assert persons is not None

    assert 2870 == len(persons)
    for p in persons.values():
        assert 'prb' == p.role


def test_pheno_tool_proband_siblings(phdb, all_ssc_studies):
    tool = PhenoTool(phdb, all_ssc_studies, roles=['sib'])
    assert tool is not None

    persons = tool.list_of_subjects()
    assert persons is not None

    assert 2696 == len(persons)
    for p in persons.values():
        assert 'sib' == p.role


def test_probands_and_siblings(phdb, all_ssc_studies):
    prb_tool = PhenoTool(phdb, all_ssc_studies, roles=['prb'])
    probands = prb_tool.list_of_subjects()
    assert 2870 == len(probands)

    sib_tool = PhenoTool(phdb, all_ssc_studies, roles=['sib'])
    siblings = sib_tool.list_of_subjects()
    assert 2696 == len(siblings)

    tool = PhenoTool(phdb, all_ssc_studies, roles=['prb', 'sib'])
    persons = tool.list_of_subjects()
    for pid, person in persons.items():
        if pid in probands:
            assert tool._assert_persons_equal(person, probands[pid])
            assert person.role == 'prb'
        else:
            assert tool._assert_persons_equal(person, siblings[pid])
            assert pid in siblings
            assert person.role == 'sib'


def test_report_wrong_probands_roles(phdb, all_ssc_studies):
    wrong_probands = set(["11664.p2", "12310.p2", "11324.p2", "11370.p2"])
    for st in all_ssc_studies:
        print(st.name)
        for fam in st.families.values():
            for person in fam.memberInOrder:
                if person.personId not in wrong_probands:
                    continue
                print(">\t{}".format(person))


def test_pheno_tool_proband_and_siblings_subjects(phdb, all_ssc_studies):
    tool = PhenoTool(phdb, all_ssc_studies, roles=['prb', 'sib'])
    assert tool is not None

    persons = tool.list_of_subjects()
    assert persons is not None

    assert 5566 == len(persons)
    for p in persons.values():
        assert 'prb' == p.role or 'sib' == p.role


def test_pheno_tool_probands_with_families(phdb, all_ssc_studies):
    tool = PhenoTool(
        phdb, all_ssc_studies, roles=['prb', 'sib', ],
        family_ids=['11664', '12310', '11324', '11370'])

    persons = tool.list_of_subjects()

    assert 10 == len(persons)
