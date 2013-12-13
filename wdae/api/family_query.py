from DAE import phDB


def get_races():
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
    return dict([(k, f if f == m else 'more-than-one-race')
                 for (k, f, m) in zip(phDB.families,
                                      phDB.get_variable('focuv.race_parents'),
                                      phDB.get_variable('mocuv.race_parents'))])


def get_pcdv_race():
    return __get_string_measure('pcdv.race')


def get_mocuv_race():
    return __get_string_measure('mocuv.race_parents')


def get_focuv_race():
    return __get_string_measure('focuv.race_parents')


def get_prb_gender():
    return __get_string_measure('Proband_Sex')


def get_sib_gender():
    return __get_string_measure('Sibling_Sex')


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


def filter_families_by_prb_gender(studies, gender):
    studies_families = __studies_familes_keys(studies)
    prb_gender_families = set([key for (key, val) in get_prb_gender().items()
                               if val == gender])
    return studies_families.intersection(prb_gender_families)


def filter_families_by_sib_gender(studies, gender):
    studies_families = __studies_familes_keys(studies)
    sib_gender_families = set([key for (key, val) in get_sib_gender().items()
                               if val == gender])
    return studies_families.intersection(sib_gender_families)

# def __filter_families_by_member_count(study, count):
#     return set([key for key, val in study.families.items()
#                 if len(val.memberInOrder) == count])


# def __filter_families_studies(studies, fun):
#     return set.union(*map(fun, studies))


# def filter_families_quad(studies):
#     return __filter_families_studies(
#         studies,
#         lambda st: __filter_families_by_member_count(st, 4))


# def filter_families_trio(studies):
#     return __filter_families_studies(
#         studies,
#         lambda st: __filter_families_by_member_count(st, 3))


# def __is_gender(fam, role, gender):
#     return any([p.role == role and p.gender == gender
#                 for p in fam.memberInOrder])


# def __filter_families_by_role_gender(study, role, gender):
#     return set([key for key, val in study.families.items()
#                 if __is_gender(val, role, gender)])


# def filter_families_by_role_gender(studies, role, gender):
#     return __filter_families_studies(
#         studies,
#         lambda st: __filter_families_by_role_gender(st, role, gender))


def __prepare_family_race_filter(data, family_filters):
    if 'familyRace' in data and data['familyRace'] in get_races():
        family_filters.append(
            lambda studies: filter_families_by_race(studies, data['familyRace'])
        )


# def __prepare_family_trio_quad(data, family_filters):
#     if 'familyQuadTrio' in data:
#         if data['familyQuadTrio'] == 'Trio':
#             family_filters.append(
#                 lambda sts: filter_families_trio(sts)
#             )
#         elif data['familyQuadTrio'] == 'Quad':
#             family_filters.append(
#                 lambda sts: filter_families_quad(sts)
#             )


def __prepare_family_prb_gender(data, family_filters):
    if 'familyPrbGender' in data:
        if data['familyPrbGender'].lower() == 'male':
            family_filters.append(
                lambda sts: filter_families_by_prb_gender(sts, 'male')
            )
        elif data['familyPrbGender'].lower() == 'female':
            family_filters.append(
                lambda sts: filter_families_by_prb_gender(sts, 'female')
            )


def __prepare_family_sib_gender(data, family_filters):
    if 'familySibGender' in data:
        if data['familySibGender'].lower() == 'male':
            family_filters.append(
                lambda sts: filter_families_by_sib_gender(sts, 'male')
            )
        elif data['familySibGender'].lower() == 'female':
            family_filters.append(
                lambda sts: filter_families_by_sib_gender(sts, 'female')
            )


def __prepare_family_verbal_iq(data, family_filters):
    iq_hi = None
    iq_lo = None

    if 'familyVerbalIqHi' in data:
        try:
            iq_hi = float(data['familyVerbalIqHi'])
        except:
            iq_hi = None

    if 'familyVerbalIqLo' in data:
        try:
            iq_lo = float(data['familyVerbalIqLo'])
        except:
            iq_lo = None

    if iq_hi is None and iq_lo is None:
        return

    if iq_lo is None:
        iq_lo = 0.0
    if iq_hi is None:
        iq_hi = float('inf')

    family_filters.append(
        lambda sts: filter_families_by_iq(sts, iq_lo, iq_hi)
    )


def prepare_family_advanced(data):
    family_filters = []
    __prepare_family_race_filter(data, family_filters)
    #__prepare_family_trio_quad(data, family_filters)
    #__prepare_family_prb_gender(data, family_filters)
    #__prepare_family_sib_gender(data, family_filters)
    __prepare_family_verbal_iq(data, family_filters)

    return family_filters


def filter_families_advanced(studies, family_filters):
    family_ids = [fun(studies) for fun in family_filters]
    return set.intersection(*family_ids)


def apply_families_advanced_filter(filters, data, studies):
    if filters['familyIds'] is None:
        family_filters = prepare_family_advanced(data)
        if len(family_filters) > 0:
            family_ids = filter_families_advanced(studies, family_filters)
            filters['familyIds'] = family_ids


def filter_variants_quad(v):
    if len(v.memberInOrder) == 4:
        return True


def filter_variants_trio(v):
    if len(v.memberInOrder) == 3:
        return True


def filter_proband_male(v):
    return v.memberInOrder[2].gender == 'M'


def filter_proband_female(v):
    return v.memberInOrder[2].gender == 'F'


def filter_sibling_male(v):
    return len(v.memberInOrder) > 3 and v.memberInOrder[3].gender == 'M'


def filter_sibling_female(v):
    return len(v.memberInOrder) > 3 and v.memberInOrder[3].gender == 'F'


def __prepare_family_prb_gender_post(data, family_filters):
    if 'familyPrbGender' in data:
        if data['familyPrbGender'].lower() == 'male':
            family_filters.append(
                filter_proband_male
            )
        elif data['familyPrbGender'].lower() == 'female':
            family_filters.append(
                filter_proband_female
            )


def __prepare_family_sib_gender_post(data, family_filters):
    if 'familySibGender' in data:
        if data['familySibGender'].lower() == 'male':
            family_filters.append(
                filter_sibling_male
            )
        elif data['familySibGender'].lower() == 'female':
            family_filters.append(
                filter_sibling_female
            )


def __prepare_family_trio_quad_post(data, family_filters):
    if 'familyQuadTrio' in data:
        if data['familyQuadTrio'].lower() == 'trio':
            family_filters.append(
                filter_variants_trio
            )
        elif data['familyQuadTrio'].lower() == 'quad':
            family_filters.append(
                filter_variants_quad
            )


def prepare_family_advanced_variants_filters(data, family_filters):
    __prepare_family_prb_gender_post(data, family_filters)
    __prepare_family_sib_gender_post(data, family_filters)
    __prepare_family_trio_quad_post(data, family_filters)
    return family_filters
