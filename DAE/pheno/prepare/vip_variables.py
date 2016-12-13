'''
Created on Dec 13, 2016

@author: lubo
'''
from pheno.prepare.vip_families import VipLoader
from pheno.prepare.base_variables import BaseVariables


class VipVariables(VipLoader, BaseVariables):

    INSTRUMENTS = [
        'abcl_18_59',
        'adi_r',
        'ados_1',
        'ados_2',
        'ados_3',
        'ados_4',
        'adult_sleep',
        'background_hx_sup',
        'bapq',
        'bsi',
        'casl_1',
        'casl_2',
        'cbcl_2_5',
        'cbcl_6_18',
        'ccc_2',
        'celf_4_f2_st',
        'celf_4_rf_1',
        'ctopp',
        'das_ii_early_years',
        'das_ii_school_age',
        'diagnosis_summary',
        'disc_yc',
        'disc_youth',
        # 'd-kefs',
        'eah_adult_self',
        'eah_child_self',
        'eah_parent_child',
        # 'education_history',
        'ehi_parent',
        'ehi_self',
        'feeding_c',
        'feeding_t',
        'growth_measurements',  # ???
        'htwhc',
        'lab_results',
        'loc_parent',
        'loc_self',
        'macarthur_words_gestures',
        'macarthur_words_sentences',
        'med_adult',
        'med_child',
        'mhi_adult',
        'mhi_ped',
        'movement_abc_2',
        'mullen',
        'nrrf',
        'pediatric_sleep',
        'pregnancy_history',
        'pregnancy_questionnaire',
        # 'previous_diagnosis',
        'psi',
        'puberty_boy',
        'puberty_girl',
        'puberty_man',
        'puberty_woman',
        'purdue_pegboard',
        's_cap',
        'scl_90_r',
        'scq_life',
        'srs_adult',
        'srs_parent',
        'svip_background_history_adult',
        'svip_background_history',
        'svip-neuro-exam',
        # 'svip_subjects',
        # ??? 'svip_summary_variables',
        # 'treatment_history',
        'vineland_ii',
        'wasi',
        'wiat_iii',
    ]

    def __init__(self, *args, **kwargs):
        super(VipVariables, self).__init__(*args, **kwargs)

    def _prepare_instrument(self, persons, instrument_name):
        idf = self.load_instrument(instrument_name)
        df = idf.join(persons, on='person_id', rsuffix="_person")

        for measure_name in df.columns[5:len(idf.columns)]:
            mdf = df[['person_id', measure_name,
                      'family_id', 'person_role']]
            self._build_variable(instrument_name, measure_name,
                                 mdf.dropna())

    def prepare(self):
        self._create_variable_table()
        self._create_value_tables()

        persons = self.load_persons_df()
        for instrument in self.INSTRUMENTS:
            self._prepare_instrument(persons, instrument)
