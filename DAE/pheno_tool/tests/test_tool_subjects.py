'''
Created on Nov 25, 2016

@author: lubo
'''
from pheno_tool.tool import PhenoTool
from pheno.common import Role


def test_pheno_tool_studies_proband_subjects(phdb, all_ssc_studies):
    tool = PhenoTool(phdb, all_ssc_studies, roles=[Role.prb],
                     measure_id='ssc_commonly_used.height')
    assert tool is not None

    persons = tool._studies_persons(all_ssc_studies, [Role.prb])
    assert persons is not None

    assert 2870 == len(persons)
    for p in persons.values():
        assert Role.prb == p.role


def test_pheno_tool_studies_siblings(phdb, all_ssc_studies):
    tool = PhenoTool(phdb, all_ssc_studies, roles=[Role.sib],
                     measure_id='ssc_commonly_used.height')
    assert tool is not None

    persons = tool._studies_persons(all_ssc_studies, [Role.sib])
    assert persons is not None

    assert 2696 == len(persons)
    for p in persons.values():
        assert Role.sib == p.role


def test_studies_probands_and_siblings(phdb, all_ssc_studies):
    probands = PhenoTool._studies_persons(all_ssc_studies, [Role.prb])
    assert 2870 == len(probands)

    siblings = PhenoTool._studies_persons(all_ssc_studies, [Role.sib])
    assert 2696 == len(siblings)

    tool = PhenoTool(phdb, all_ssc_studies, roles=[Role.prb, Role.sib],
                     measure_id='ssc_commonly_used.height')
    persons = PhenoTool._studies_persons(all_ssc_studies, [Role.prb, Role.sib])
    for pid, person in persons.items():
        if pid in probands:
            assert tool._assert_persons_equal(person, probands[pid])
            assert person.role == Role.prb
        else:
            assert tool._assert_persons_equal(person, siblings[pid])
            assert pid in siblings
            assert person.role == Role.sib


def test_report_wrong_probands_roles(all_ssc_studies):
    wrong_probands = set(["11664.p2", "12310.p2", "11324.p2", "11370.p2"])
    for st in all_ssc_studies:
        for fam in st.families.values():
            for person in fam.memberInOrder:
                if person.personId not in wrong_probands:
                    continue


def test_studies_proband_and_siblings_subjects(phdb, all_ssc_studies):
    tool = PhenoTool(phdb, all_ssc_studies, roles=[Role.prb, Role.sib],
                     measure_id='ssc_commonly_used.height')
    assert tool is not None

    persons = PhenoTool._studies_persons(all_ssc_studies, [Role.prb, Role.sib])
    assert persons is not None

    assert 5566 == len(persons)
    for p in persons.values():
        assert Role.prb == p.role or Role.sib == p.role


def test_list_of_subjects(phdb, all_ssc_studies):
    tool = PhenoTool(phdb, all_ssc_studies, roles=[Role.prb, Role.sib],
                     measure_id='ssc_commonly_used.height')
    persons = tool.list_of_subjects()
    assert 5177 == len(persons)

    tool = PhenoTool(phdb, all_ssc_studies, roles=[Role.prb],
                     measure_id='ssc_commonly_used.height')
    persons = tool.list_of_subjects()
    assert 2726 == len(persons)

    tool = PhenoTool(phdb, all_ssc_studies, roles=[Role.sib],
                     measure_id='ssc_commonly_used.height')
    persons = tool.list_of_subjects()
    assert 2451 == len(persons)

# def test_pheno_tool_probands_with_families(phdb, all_ssc_studies):
#     tool = PhenoTool(
#         phdb, all_ssc_studies, roles=['prb', 'sib', ],
#         family_ids=['11664', '12310', '11324', '11370'])
#
#     persons = tool.list_of_subjects()
#
#     assert 10 == len(persons)
