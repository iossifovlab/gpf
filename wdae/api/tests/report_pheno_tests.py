import unittest

from api.report_pheno import pheno_query_variants, pheno_query, \
    get_pheno_measure, get_verbal_iq, get_non_verbal_iq, \
    get_supported_measures, get_supported_studies, \
    pheno_calc

from query_prepare import prepare_denovo_studies

class PhenoTest(unittest.TestCase):
    TEST_DATA = {"denovoStudies": "ALL SSC",
                 "measure": "NvIQ"}

    def test_variants(self):
        vs = pheno_query_variants(self.TEST_DATA)
        self.assertTrue(vs)

    def test_studies(self):
        stds = prepare_denovo_studies(self.TEST_DATA)
        print(stds)
        self.assertTrue(stds)

    def test_pheno_query(self):
        ps = pheno_query(self.TEST_DATA)
        for p in ps:
            self.assertTrue(p)
            # print(p)


    def test_pheno_measures(self):
        NVIQ = get_pheno_measure("pcdv.ssc_diagnosis_nonverbal_iq", float)
        # print(NVIQ)
        self.assertTrue(NVIQ)
        VIQ = get_pheno_measure("pcdv.ssc_diagnosis_verbal_iq", float)
        # print(VIQ)
        self.assertTrue(VIQ)
        seizures_proband = get_pheno_measure('pumhx.medhx_fam_neurological.seizures_proband')
        dysmorphyic_proband = get_pheno_measure('padm2.dysmorphic_yes_no')
        # print(seizures_proband)
        # print(dysmorphyic_proband)

        self.assertTrue(seizures_proband)
        self.assertTrue(dysmorphyic_proband)

        self.assertTrue(get_verbal_iq())
        self.assertTrue(get_non_verbal_iq())

    def test_get_pheno_studies(self):
        stds = get_supported_studies()
        print(stds)

    def test_get_supported_measures(self):
        supp_measures = get_supported_measures()
        print(supp_measures)

    def test_pheno_calc(self):
        ps = pheno_query(self.TEST_DATA)
        res = pheno_calc(ps)
        print(res)