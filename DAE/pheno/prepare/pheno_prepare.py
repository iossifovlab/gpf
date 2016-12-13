'''
Created on Sep 14, 2016

@author: lubo
'''
from pheno.prepare.families import PrepareIndividuals, \
    PrepareIndividualsGender,\
    PrepareIndividualsSSCPresent, PrepareIndividualsGenderFromSSC,\
    CheckIndividualsGenderToSSC
from pheno.prepare.variables import PrepareVariables
from pheno.prepare.values import PrepareRawValues, \
    PrepareValueClassification
from pheno.prepare.pheno_common import PreparePhenoCommonAge,\
    PreparePhenoCommonRace, PreparePhenoIQ

LINE = "--------------------------------------------------------------------"


def prepare_pheno_families_cache():
    print(LINE)
    print("prepare pheno db family caches")
    print(LINE)

    p10 = PrepareIndividuals()
    p10.prepare()

    p20 = PrepareIndividualsGender()
    p20.prepare()

    p30 = PrepareIndividualsSSCPresent()
    p30.prepare()

    p40 = PrepareIndividualsGenderFromSSC()
    p40.prepare()

    print(LINE)


def prepare_pheno_variables_cache():
    print(LINE)
    print("prepare pheno db variable dictionary caches")
    print(LINE)

    p10 = PrepareVariables()
    p10.prepare()

    print(LINE)


def prepare_pheno_raw_values_cache():
    print(LINE)
    print("prepare pheno db raw values caches")
    print(LINE)

    p20 = PrepareRawValues()
    p20.prepare()

    print(LINE)


def classify_pheno_variables():
    print(LINE)
    print("prepare pheno db variable classification caches")
    print(LINE)

    p20 = PrepareValueClassification()
    p20.prepare()

    print(LINE)


def prepare_pheno_common():
    print(LINE)
    print("prepare pheno common variables")
    print(LINE)

    p20 = PreparePhenoCommonAge()
    p20.prepare()

    p30 = PreparePhenoCommonRace()
    p30.prepare()

    p40 = PreparePhenoIQ()
    p40.prepare()

    print(LINE)


def check_pheno_families_cache():
    print(LINE)
    print("checking pheno db caches")
    print(LINE)

    ch10 = CheckIndividualsGenderToSSC()
    ch10.check()

    print(LINE)


def prepare_pheno_db_cache():
    prepare_pheno_families_cache()
    prepare_pheno_variables_cache()
    prepare_pheno_raw_values_cache()
    prepare_pheno_common()
    classify_pheno_variables()


def check_pheno_db_cache():
    check_pheno_families_cache()


def prepare_agre_families():
    import agre_families
    p = agre_families.PrepareIndividuals()
    p.prepare()


def prepare_agre_variables():
    import agre_variables
    p = agre_variables.PrepareVariables()
    p.prepare()


def prepare_agre_pheno_db():
    prepare_agre_families()
    prepare_agre_variables()


def prepare_agre_pheno_db_meta():
    import agre_meta
    p = agre_meta.PrepareMetaVariables()
    p.prepare()


def prepare_vip_pheno_db():
    import vip_families
    p = vip_families.PrepareIndividuals()
    p.prepare()

    import vip_variables
    p = vip_variables.VipVariables()
    p.prepare()
