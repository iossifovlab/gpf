import pytest, os
from test_get_pheno_property import measure_query, people_query, \
                                    column_name2property

def get_simple_ids(arr):
    res = []
    for prp in arr:
        res.append(prp + 'TestString')
        res.append('Multiple-' + prp + 'TestString')
    return res

def arg2str(k,v):
    return k+'=' + ','.join(v) + ';'

def get_complex_ids(arr):
    res = []
    for d in arr:
        res.append(' '.join([arg2str(k,v) for k,v in d.items()]))
    return res


'''INSTRUMENT PARSER TEST CASES'''
@pytest.fixture(params=['spark', 'spark,vip'],
                ids=get_simple_ids(['PhenoDb']))
def instrument_dbs_cases(request):
    return request.param

@pytest.fixture(params=['asd', 'asd,fgh'],
                ids=get_simple_ids(['IncorrectPhenoDb']))
def instrument_incorrect_dbs_cases(request):
    return request.param

@pytest.fixture(params=[
                {'input':'agre,asd', 'expected':'agre'},
                {'input':'spark,asd,fgh,vip', 'expected':'spark,vip'}],
                ids=get_simple_ids(['MixedIncorrectPhenoDb']))
def instrument_partially_incorrect_input_dbs_cases(request):
    return request.param


'''MEASURES PARSER TEST CASES'''
def get_measures_simple_cases():
    return [
        {'Db' : ['spark']},
        {'Db' : ['spark','vip']},
        {'Instrument' : ['scq']},
        {'Instrument' : ['scq','individuals']},
        {'Type' : ['ordinal']},
        {'Type' : ['ordinal','continuous']},
        {'MeasureId' : ['individuals.cognitive_impairment']},
        {'MeasureId' : ['scq.role','scq.asd']}
    ]
@pytest.fixture(params=get_measures_simple_cases(),
                ids=get_simple_ids(
                ['PhenoDb', 'Instruments', 'MeasureTypes', 'MesureIds']))
def measures_simple_cases(request):
    return measure_query(request.param), request.param

def get_measures_complex_cases():
    return [
        {'Db' : ['spark'], 'Instrument' : ['scq'], 'Type' : ['ordinal']},
        {'Db' : ['spark'], 'Instrument' : ['scq'], 'Type' : ['categorical'],
        'MeasureId' : ['scq.asd']},
        {'Instrument' : ['individuals'],
        'MeasureId' : ['individuals.role','individuals.asd']},
        {'Db' : ['spark'], 'MeasureId' : ['scq.q34_copy_actions','individuals.asd'],
        'Type' : ['ordinal']}
    ]
@pytest.fixture(params=get_measures_complex_cases(),
                ids=get_complex_ids(get_measures_complex_cases()))
def measures_complex_cases(request):
    expected = request.param
    if 'MeasureId' in expected and \
        expected['MeasureId'] == ['scq.q34_copy_actions','individuals.asd']:
        expected['MeasureId'].pop()
    return measure_query(request.param), expected

def get_measures_filtered_until_empty_cases():
    return [
        {'Db' : ['spark'], 'Type' : ['unknown']},
        {'MeasureId' : ['individuals.role'], 'Type' : ['ordinal']} #true type: categorical
    ]
@pytest.fixture(params=get_measures_filtered_until_empty_cases(),
                ids=get_complex_ids(get_measures_filtered_until_empty_cases()))
def measures_filtered_until_empty_cases(request):
    return measure_query(request.param)

def get_measures_incorrect_input_cases():
    return [
        {'Instrument' : ['asd']},
        {'Type' : ['asd']},
        {'MeasureId' : ['asd']},
        {'MeasureId' : ['asd'], 'Instrument' : ['asd'], 'Type' : ['asd']}
    ]
@pytest.fixture(params=get_measures_incorrect_input_cases(),
                ids=get_complex_ids(get_measures_incorrect_input_cases()))
def measures_incorrect_input_cases(request):
    return measure_query(request.param)

def get_measures_partially_incorrect_input_cases():
    return [
        {'Instrument' : ['scq','asd']},
        {'Type' : ['ordinal','asd']},
        {'MeasureId' : ['scq.role','asd']},
        {'MeasureId' : ['scq.role','asd'],
        'Instrument' : ['scq','asd'], 'Type' : ['categorical','asd']}
    ]
@pytest.fixture(params=get_measures_partially_incorrect_input_cases(),
                ids=get_complex_ids(
                    get_measures_partially_incorrect_input_cases()))
def measures_partially_incorrect_input_cases(request):
    expected = request.param
    for k in expected: expected[k].pop()
    return measure_query(request.param), expected


'''PEOPLE PARSER TEST CASES'''
def path(s):
    p = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(p, s)

def get_people_file_input_cases():
    m = {'MeasureId' : ['individuals.age_at_registration_years']} #for speediness
    p1, p2 = path('pheno/person-ids2.txt'), path('pheno/person-ids.txt')
    f1, f2 = path('pheno/family-ids.txt'), path('pheno/family-ids2.txt')
    return [
        (dict({'personIdsFile' : [p1]}, **m),
            dict({'person_id' : ['SP0043589']}, **m)),
        ({'personIdsFile' : [p1, p2], 'MeasureId' :
                ['individuals.age_at_registration_years,ADOSToddler1.INTON']},
            {'person_id' : ['SP0043589', 'SP0026379']}),
        (dict({'familyIdsFile' : [f1]}, **m),
            dict({'family_id' : ['SF0068842', 'SF0038472']}, **m)),
        (dict({'familyIdsFile' : [f1, f2]}, **m),
            dict({'family_id' : ['SF0068842', 'SF0038472']}, **m))
    ]
@pytest.fixture(params=get_people_file_input_cases(),
                ids=get_simple_ids(['PersonIdsFile', 'FamilyIdsFile']))
def people_file_input_cases(request):
    return people_query(request.param[0]), request.param[1]

def get_people_simple_cases():
    return [
        {'Db' : ['spark']},
        {'Db' : ['spark','vip']},
        {'status' : ['affected']},
        {'status' : ['affected','unaffected']},
        {'Instrument' : ['individuals']},
        {'Instrument' : ['scq','individuals']},
        {'Type' : ['continuous']},
        {'Type' : ['continuous','unknown']},
        {'MeasureId' : ['scq.asd']},
        {'MeasureId' : ['scq.asd', 'individuals.age_at_registration_years']},
        {'family_id' : ['SF0068842']},
        {'family_id' : ['SF0068842', 'SF0038472']},
        {'role' : ['mom']},
        {'role' : ['sib','dad']},
        {'gender' : ['M']},
        {'gender' : ['M','F']},
        {'person_id' : ['SP0026379']},
        {'person_id' : ['SP0026379', 'SP0043589']}
    ]
@pytest.fixture(params=get_people_simple_cases(),
                ids=get_complex_ids(get_people_simple_cases()))
def people_simple_cases(request):
    return people_query(request.param), request.param

def get_people_complex_cases():
    return [
        {'Db' : ['spark'],
        'Instrument' : ['scq'],
        'role': ['prb']},
        {'Db' : ['spark'],
        'Instrument' : ['individuals'],
        'Type' : ['continuous']},
        {'Db' : ['agre'],
        'Type' : ['categorical'],
        'role' : ['prb'],
        'gender' : ['M'],
        'status' : ['affected'],
        },
        {'Db' : ['spark'],
        'Type' : ['continuous'],
        'role' : ['prb'],
        'gender' : ['M'],
        'status' : ['affected'],
        'Instrument' : ['individuals'],
        'MeasureId' : ['individuals.age_at_registration_years'],
        },
        {'Db' : ['agre'],
        'Type' : ['categorical'],
        'role' : ['prb'],
        'gender' : ['M'],
        'status' : ['affected'],
        'person_id' : ['AU1210302','AU3599303','AU3054301'],
        'family_id' : ['AU3054', 'AU1503'],
        'Instrument' : ['Hands1','Mullen1'],
        'MeasureId' : ['Hands1.ProjectName', 'AffChild1.Previous_Alcohol_Comment']
        },
        {'Db' : ['agre'],
        'MeasureId' : ['AffChild1.Maternal_med_4_dose_comment'],
        'person_id' : ['AU1088302'],
        'family_id' : ['AU1088']},
        {'Db' : ['agre'],
        'Type' : ['categorical'],
        'role' : ['prb'],
        'gender' : ['M'],
        'status' : ['affected'],
        'Instrument' : ['AffChild1', 'MotherH1'],
        'MeasureId' : ['AffChild1.Prev_Sup_4_dose_comment']}
    ]
@pytest.fixture(params=get_people_complex_cases(),
                ids=get_complex_ids(get_people_complex_cases()))
def people_complex_cases(request):
    expected = request.param
    if 'family_id' in expected and expected['family_id'] == ['AU3054', 'AU1503']:
        expected['family_id'].pop()
        expected['person_id'] = ['AU3054301']
    return people_query(request.param), expected

def get_people_incorrect_input_cases():
    m = {'MeasureId' : ['individuals.age_at_registration_years']} #for speediness
    single, multiple = ['incorrect'], ['inc1','inc2']
    single_dicts = [dict({k:single},**m) for k in column_name2property
                    if 'File' not in k and k != 'MeasureId']
    multiple_dicts = [dict({k:multiple},**m) for k in column_name2property
                    if 'File' not in k and k != 'MeasureId']
    single_dicts.append({'MeasureId': ['incorrect']})
    multiple_dicts.append({'MeasureId': ['incorrect']})
    return single_dicts + multiple_dicts
@pytest.fixture(params=get_people_incorrect_input_cases(),
                ids=get_complex_ids(get_people_incorrect_input_cases()))
def people_incorrect_input_cases(request):
    return people_query(request.param)

def get_people_filter_until_empty_cases():
    return [
        {'Db' : ['spark'],
        'Instrument' : ['scq'],
        'role' : ['mom']},
        {'Db' : ['agre'],
        'Type' : ['ordinal'],
        'Instrument' : ['AffChild1', 'MotherH1'],
        'MeasureId' : ['AffChild1.Prev_Sup_4_dose_comment']}
    ]
@pytest.fixture(params=get_people_filter_until_empty_cases(),
                ids=get_complex_ids(get_people_filter_until_empty_cases()))
def people_filter_until_empty_cases(request):
    return people_query(request.param)

def get_people_partially_incorrect_input_cases():
    m = {'MeasureId' : ['individuals.age_at_registration_years']} #for speediness
    return [
        dict({'Db' : ['spark','incorrect']}, **m),
        dict({'status' : ['affected','incorrect']}, **m),
        dict({'Instrument' : ['individuals','incorrect']}, **m),
        dict({'Type' : ['continuous','incorrect']}, **m),
        {'MeasureId' : ['scq.asd', 'incorrect']},
        dict({'family_id' : ['SF0068842', 'incorrect']}, **m),
        dict({'role' : ['sib','incorrect']}, **m),
        dict({'gender' : ['M','incorrect']}, **m),
        dict({'person_id' : ['SP0026379', 'incorrect']}, **m)
    ]
@pytest.fixture(params=get_people_partially_incorrect_input_cases(),
                ids=get_complex_ids(get_people_partially_incorrect_input_cases()))
def people_partially_incorrect_input_cases(request):
    expected = request.param
    for k in expected:
        if k != 'MeasureId': expected[k].pop()
    if len(expected['MeasureId']) == 2: expected['MeasureId'].pop()
    return people_query(request.param), expected
