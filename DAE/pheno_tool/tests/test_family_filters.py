'''
Created on Nov 15, 2016

@author: lubo
'''


def test_verbal_iq_interval(phdb, family_filters):
    family_ids = family_filters.get_measure_families(
        'ssc_core_descriptive.ssc_diagnosis_verbal_iq', 10, 11)
    assert 15 == len(family_ids)

    df = phdb.get_measure_values_df(
        'ssc_core_descriptive.ssc_diagnosis_verbal_iq', roles=['prb'])

    for family_id in family_ids:
        index = df['person_id'].str.startswith(family_id)
        assert all(
            df[index][
                'ssc_core_descriptive.ssc_diagnosis_verbal_iq'
            ].values <= 11)
        assert all(
            df[index][
                'ssc_core_descriptive.ssc_diagnosis_verbal_iq'
            ].values >= 10)


def test_head_circumference_interval(phdb, family_filters):
    family_ids = family_filters.get_measure_families(
        'ssc_commonly_used.head_circumference', 49, 50)
    assert 102 == len(family_ids)
    df = phdb.get_measure_values_df(
        'ssc_commonly_used.head_circumference', roles=['prb'])
    for family_id in family_ids:
        index = df['person_id'].str.startswith(family_id)
        assert all(
            df[index]['ssc_commonly_used.head_circumference'].values <= 50)
        assert all(
            df[index]['ssc_commonly_used.head_circumference'].values >= 49)


def test_verbal_iq_interval_with_family_counters(phdb, family_filters):
    proband_ids = family_filters.get_measure_probands(
        'ssc_core_descriptive.ssc_diagnosis_verbal_iq', 10, 11)

    assert 15 == len(proband_ids)
    df = phdb.get_measure_values_df(
        'ssc_core_descriptive.ssc_diagnosis_verbal_iq', roles=['prb'])
    for proband_id in proband_ids:
        assert all(
            df[df['person_id'] ==
               proband_id][
                'ssc_core_descriptive.ssc_diagnosis_verbal_iq'
            ].values <= 11)
        assert all(df[df['person_id'] ==
                      proband_id][
                          'ssc_core_descriptive.ssc_diagnosis_verbal_iq'
        ].values >= 10)
