'''
Created on Apr 26, 2016

@author: lubo
'''
from DAE import vDB


def get_ssc_all_group():
    return 'ALL SSC'


def get_ssc_all():
    study_group = vDB.get_study_group(get_ssc_all_group())

    denovo_studies = study_group.get_attr('studies')
    transmitted_studies = study_group.get_attr('transmittedStudies')

    return {"denovoStudies": denovo_studies,
            "transmittedStudies": transmitted_studies}


def get_ssc_denovo():
    res = get_ssc_all()
    return res['denovoStudies']


def get_ssc_transmitted():
    res = get_ssc_all()
    return res['transmittedStudies']


def get_ssc_all_studies():
    study_group = vDB.get_study_group(get_ssc_all_group())

    denovo_studies = vDB.get_studies(
        study_group.get_attr('studies'))
    transmitted_name = study_group.get_attr('transmittedStudies')
    if transmitted_name is None:
        transmitted_studies = None
    else:
        transmitted_studies = vDB.get_studies(transmitted_name)

    return {"denovoStudies": denovo_studies,
            "transmittedStudies": transmitted_studies}


def get_ssc_denovo_studies():
    res = get_ssc_all_studies()
    return res['denovoStudies']


def get_ssc_transmitted_studies():
    res = get_ssc_all_studies()
    return res['transmittedStudies']
