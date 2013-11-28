from DAE import phDB


def __get_races():
    return {'african-amer',
            'asian',
            'more-than-one-race',
            'native-american',
            'native-hawaiian',
            'white'}


def __get_float_measure(var_name):
    str_map = dict(zip(phDB.families, phDB.get_variable(var_name)))
    flt_map = {}
    for key, val in str_map.items():
        try:
            flt_map[key] = float(val)
        except:
            pass
    return flt_map


def __get_string_measure(mName):
    return dict(zip(phDB.families, phDB.get_variable(mName)))


def get_verbal_iq():
    return __get_float_measure('pcdv.ssc_diagnosis_verbal_iq')


def get_non_verbal_iq():
    return __get_float_measure('pcdv.ssc_diagnosis_nonverbal_iq')


def get_parents_race():
    return __get_string_measure('focuv.race_parents')


def get_pcdv_race():
    return __get_string_measure('pcdv.race')


def get_mocuv_race():
    return __get_string_measure('mocuv.race_parents')


def get_focuv_race():
    return __get_string_measure('focuv.race_parents')


def __studies_familes_keys(studies):
    lst = [set(st.families.keys()) for st in studies]
    return set.union(*lst)


def filter_families_by_race(studies, race):
    study_families = __studies_familes_keys(studies)
    return set([key for key, val in get_parents_race().items()
                if key in study_families and val == race])


def filter_families_by_iq(studies, iq_lo=0.0, iq_hi=float('inf')):
    study_families = __studies_familes_keys(studies)
    return set([key for key, val in get_verbal_iq().items()
                if val >= iq_lo and val <= iq_hi and key in study_families])


def __filter_families_by_member_count(study, count):
    return set([key for key, val in study.families.items()
                if len(val.memberInOrder) == count])


def __filter_families_studies(studies, fun):
    return set.union(*map(fun, studies))


def filter_families_quad(studies):
    return __filter_families_studies(
        studies,
        lambda st: __filter_families_by_member_count(st, 4))


def filter_families_trio(studies):
    return __filter_families_studies(
        studies,
        lambda st: __filter_families_by_member_count(st, 3))


def __is_gender(fam, role, gender):
    return any([p.role == role and p.gender == gender
                for p in fam.memberInOrder])


def __filter_families_by_role_gender(study, role, gender):
    return set([key for key, val in study.families.items()
                if __is_gender(val, role, gender)])


def filter_families_by_role_gender(studies, role, gender):
    return __filter_families_studies(
        studies,
        lambda st: __filter_families_by_role_gender(st, role, gender))
