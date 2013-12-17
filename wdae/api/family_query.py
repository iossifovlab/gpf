from DAE import phDB

import logging

logger = logging.getLogger(__name__)


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


def family_filter_by_race(families, race):
    races = get_parents_race()
    res = dict([(key, val) for (key, val) in families.items()
                if key in races and races[key] == race])
    # logger.debug("family_filter_by_race: %s", str(res))
    return res


def __bind_family_filter_by_race(data, family_filters):
    if 'familyRace' in data and data['familyRace'].lower() != 'all':
        family_filters.append(
            lambda fs: family_filter_by_race(fs, data['familyRace'])
        )


def study_family_filter_by_verbal_iq(families, iq_lo=0.0, iq_hi=float('inf')):
    return dict([(key, families[key]) for key, val in get_verbal_iq().items()
                if key in families and val >= iq_lo and val <= iq_hi])


def __bind_family_filter_by_verbal_iq(data, family_filters):
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
        lambda fs: study_family_filter_by_verbal_iq(fs, iq_lo, iq_hi)
    )


def study_family_filter_by_prb_gender(families, gender):
    return dict([(key, val) for (key, val) in families.items()
                 if val.memberInOrder[2].gender == gender])


def __bind_family_filter_by_prb_gender(data, family_filters):
    if 'familyPrbGender' in data:
        if data['familyPrbGender'].lower() == 'male':
            family_filters.append(
                lambda fs: study_family_filter_by_prb_gender(fs, 'M')
            )
        elif data['familyPrbGender'].lower() == 'female':
            family_filters.append(
                lambda fs: study_family_filter_by_prb_gender(fs, 'F')
            )


def study_family_filter_by_sib_gender(families, gender):
    return dict([(key, val) for (key, val) in families.items()
                 if len(val.memberInOrder) > 3
                 and val.memberInOrder[3].gender == gender])


def __bind_family_filter_by_sib_gender(data, family_filters):
    if 'familySibGender' in data:
        if data['familySibGender'].lower() == 'male':
            family_filters.append(
                lambda fs: study_family_filter_by_sib_gender(fs, 'M')
            )
        elif data['familySibGender'].lower() == 'female':
            family_filters.append(
                lambda fs: study_family_filter_by_sib_gender(fs, 'F')
            )


def study_family_filter_by_trio_quad(families, trio_quad):
    """
    Filters dictionary of families by number of family members.
    Returns dictionary of families, for which number of members is equal
    to 'trio_quad' parameter of the function.
    """
    return dict([(key, val) for (key, val) in families.items()
                 if len(val.memberInOrder) == trio_quad])


def __bind_family_filter_by_trio_quad(data, family_filters):
    if 'familyQuadTrio' in data:
        if data['familyQuadTrio'].lower() == 'trio':
            logger.debug("filtering trio families...")
            family_filters.append(
                lambda fs: study_family_filter_by_trio_quad(fs, 3)
            )
        elif data['familyQuadTrio'].lower() == 'quad':
            logger.debug("filtering quad families...")
            family_filters.append(
                lambda fs: study_family_filter_by_trio_quad(fs, 4)
            )


def __apply_family_filters(study, family_filters):
    if family_filters is None or len(family_filters) == 0:
        return None
    families = study.families
    for ff in family_filters:
        families = ff(families)
    return families


def advanced_family_filter(data, filters):
    if 'familyIds' in filters and filters['familyIds'] is not None \
       and len(filters['familyIds']) > 0:
        return None

    family_filters = []
    __bind_family_filter_by_race(data, family_filters)
    __bind_family_filter_by_verbal_iq(data, family_filters)
    __bind_family_filter_by_trio_quad(data, family_filters)
    __bind_family_filter_by_prb_gender(data, family_filters)
    __bind_family_filter_by_sib_gender(data, family_filters)
    # logger.debug("family filters: %d", len(family_filters))

    if len(family_filters) == 0:
        return None
    else:
        return lambda study: __apply_family_filters(study, family_filters)
