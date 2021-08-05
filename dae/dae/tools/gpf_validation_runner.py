import argparse
import os
import io
import sys
import glob
import yaml
import time
import logging
import copy
import enum
import pandas as pd

from xml.etree.ElementTree import Element, tostring

from dae.gpf_instance.gpf_instance import GPFInstance


class TestStatus(enum.Enum):
    NOTSET = 0
    PASSED = 1
    FAIL = 2
    ERROR = 4


class TestResult:
    def __init__(
            self,
            expectation=None,
            case=None,
            test_for=None,
            params=None,
            result=None,
            expected=None):

        self.expectation = expectation
        self.case = case
        self.test_for = test_for
        self.params = params
        self.status = TestStatus.NOTSET
        self.expected = expected
        self.result = result
        self.message = None
        self.time = None

    def __str__(self):
        out = f"{self.study} {self.test_for} test {self.case_number} "
        if self.status == TestStatus.PASSED:
            out += "PASSED"
        elif self.status == TestStatus.FAIL:
            out += f"FAILED: expected {self.expected},"
        elif self.status == TestStatus.ERROR:
            out += "ERROR"
        return out

    def to_xml_element(self):
        testcase = Element("testcase")
        case_name = self.case["name"]
        filename = self.expectation["file"]
        study_id = self.expectation["study"]
        target = self.expectation["target"]

        name = f"Case {case_name}: {self.test_for}"
        for param, value in self.params.items():
            if isinstance(value, list):
                value_str = ",".join([str(v) for v in value])
            else:
                value_str = str(value)
            name += f"|{param}[{value_str}]"
        testcase.set("name", str(name))
        testcase.set("time", str(self.time))
        testcase.set("filename", filename)
        testcase.set(
            "classname",
            f"{study_id}:{target}:{name}"
        )
        if self.status == TestStatus.PASSED:
            pass
        elif self.status == TestStatus.FAIL:
            failure = Element("failure")
            failure.set(
                "message",
                f"Expected {self.expected}, Got {self.result}")
            testcase.append(failure)
        elif self.status == TestStatus.ERROR:
            error = Element("error")
            error.set(
                "message",
                f"Expected {self.expected}, Got {self.result}")
            testcase.append(error)
        return testcase


class TestSuite:
    def __init__(self, study, target, name):
        self.study = study
        self.name = name
        self.target = target
        self.cases = list()

    def append(self, case):
        self.cases.append(case)

    def to_xml_element(self):
        testsuite = Element("testsuite")
        testsuite.set("name", f"{self.study} {self.target}: {self.name}")
        testsuite.set("tests", str(len(self.cases)))
        failures = \
            len(list(filter(lambda x: x.status == TestStatus.FAIL, self.cases)))
        testsuite.set("failures", str(failures))

        for case in self.cases:
            testsuite.append(case.to_xml_element())
        return testsuite


class AbstractRunner:

    def __init__(self, expectations, gpf_instance):

        self.expectations = expectations
        self.gpf_instance = gpf_instance
        # self.failed_case_count = 0
        # self.passed_case_count = 0
        self.test_suites = []
        assert self.gpf_instance

    def _counter(self, status):
        count = 0
        for suite in self.test_suites:
            for case in suite.cases:
                if case.status == status:
                    count += 1
        return count

    @property
    def failed_case_count(self):
        return self._counter(TestStatus.FAIL)

    @property
    def passed_case_count(self):
        return self._counter(TestStatus.PASSED)

    @property
    def error_case_count(self):
        return self._counter(TestStatus.ERROR)

    # def get_xml(self):
    #     root = Element("testsuites")
    #     for suite in self.test_suites:
    #         root.append(suite.to_xml_element())
    #     return tostring(root, encoding="utf8", method="xml")


class BaseGenotypeBrowserRunner(AbstractRunner):

    def __init__(self, expectations, gpf_instance):

        super(BaseGenotypeBrowserRunner, self).__init__(
            expectations, gpf_instance)

    def _parse_frequency(self, params):
        if "frequency" not in params:
            return params
        freq = params.pop("frequency")
        assert "frequency" not in params, params
        if freq.get("ultra_rare"):
            params["ultra_rare"] = True
            assert "min" not in freq
            assert "max" not in freq
            return params

        assert "max" in freq or "min" in freq, freq
        freq_min = freq.get("min")
        freq_max = freq.get("max")

        params["frequency_filter"] = [
            ("af_allele_freq", (freq_min, freq_max))]

        return params

    def _parse_genomic_scores(self, params):
        if "genomic_scores" not in params:
            return params
        scores = params.pop("genomic_scores")
        assert "genomic_scores" not in params, params

        result = []
        for score in scores:
            assert "score" in score
            assert "max" in score or "min" in score, score
            score_min = score.get("min")
            score_max = score.get("max")

            result.append((score.get("score"), (score_min, score_max)))
        if len(result) == 0:
            return params

        params["real_attr_filter"] = result
        return params


class GenotypeBrowserRunner(BaseGenotypeBrowserRunner):

    def __init__(self, expectations, gpf_instance):

        super(GenotypeBrowserRunner, self).__init__(
            expectations, gpf_instance)

    # def _validate_families_report(self, expectation):
    #     study_id = expectation["study"]
    #     cases = expectation["cases"]
    #     file = expectation["file"]
    #     target = expectation["target"]

    #     test_suite = TestSuite(study_id, target)
    #     self.test_suites.append(test_suite)

    #     for case_number, case in enumerate(cases):
    #         start = time.time()
    #         params = case["params"]
    #         sex = None
    #         collection = params["collection_id"]
    #         value = params["collection_value"]
    #         if "sex" in params:
    #             sex = Sex.from_name(params["sex"])
    #         print("--------------------------------")
    #         print(f"Querying with params {params}")

    #         expected = case["expected"]

    #         if "count" in expected:
    #             count = expected["count"]

    #             facade = self.instance._common_report_facade
    #             persons = facade.query_person_counters(
    #                 study_id, collection, value, sex=sex
    #             )

    #             person_count = len(persons)

    #             test_result = TestResult(
    #                     study_id,
    #                     file,
    #                     target,
    #                     "count",
    #                     case_number,
    #                     params,
    #                     expected,
    #                     person_count
    #             )

    #             print(f"Expected {count} persons")
    #             if person_count == count:
    #                 test_result.success = True
    #                 print("PASSED")
    #             else:
    #                 test_result.success = False
    #                 print(f"Got: {person_count}")
    #                 self.failed_case_count += 1

    #             end = time.time()
    #             test_result.time = (end-start)
    #             test_suite.append(test_result)

    # def _validate_denovo_reports(self, expectation):
    #     study_id = expectation["study"]
    #     cases = expectation["cases"]
    #     file = expectation["file"]
    #     target = expectation["target"]

    #     test_suite = TestSuite(study_id, target)

    #     for case_number, case in enumerate(cases):
    #         start = time.time()
    #         params = case["params"]
    #         collection = params["collection_id"]
    #         value = params["collection_value"]
    #         effect_type = params["effect_type"]
    #         print("--------------------------------")
    #         print(f"Querying with params {params}")

    #         expected = case["expected"]

    #         if "count" in expected:
    #             count = expected["count"]

    #             facade = self.instance._common_report_facade
    #             results = facade.query_denovo_reports(
    #                 study_id, collection, value, effect_type
    #             )

    #             person_count = results["number_of_observed_events"]

    #             test_result = TestResult(
    #                     study_id,
    #                     file,
    #                     target,
    #                     "count",
    #                     case_number,
    #                     params,
    #                     expected,
    #                     person_count
    #             )

    #             print(f"Expected {count} persons")
    #             if person_count == count:
    #                 test_result.success = True
    #                 print("PASSED")
    #             else:
    #                 test_result.success = False
    #                 print(f"Got: {person_count}")
    #                 self.failed_case_count += 1
    #             end = time.time()
    #             test_result.time = (end-start)
    #             test_suite.append(test_result)

    #     self.test_suites.append(test_suite)

    def _build_case_expections_filename(self, case):
        dirname, _ = os.path.splitext(self.expectations["file"])
        print(dirname)
        os.makedirs(dirname, exist_ok=True)
        return os.path.join(dirname, f"{case['id']}.tsv")

    @staticmethod
    def _cleanup_allele_attributes(vprops):
        cleanup_names = [
            'ACMG_v2', 'ASC', 'BrainCriticalGene', 'CUMC', 
            'CUMC_Autism_Dmis_CADD25_Rate', 'CUMC_Autism_Dmis_REVEL0.5_Rate', 
            'CUMC_Autism_LoF_Rate', 'CUMC_DenovoWEST_tada', 'CUMC_HGNC', 
            'CUMC_NDD_Dmis_CADD25_Rate', 'CUMC_NDD_Dmis_REVEL0.5_Rate', 
            'CUMC_NDD_LoF_Rate', 'CUMC_SPARK_Dmis_CADD25', 
            'CUMC_SPARK_Dmis_REVEL0.5', 'CUMC_SPARK_LoF', 'CUMC_called_by', 
            'CUMC_pDenovoWEST', 'CUMC_pDenovoWEST_cat', 
            'CUMC_tadaDmis_predProb', 'CUMC_tadaDmis_predProb_cat', 
            'CUMC_tada_predProb', 'CUMC_tada_predProb_cat', 
            'ChromatinModifiers', 'Coe2019', 'DDD_category', 
            'DP_alt', 'DP_ref', 'EssentialGenes', 'FILTER', 
            'FMRPTargets_fragileXprotein', 'HI_interactions', 
            'LOF.GENE', 'LOF.GENEID', 'LOF.NUMTR', 'LOF.PERC', 'MPC', 
            'MendelianDiseaseGenes', 'NMD.GENE', 'NMD.GENEID', 'NMD.NUMTR', 
            'NMD.PERC', 'PreferentialEmbryonicExpressed', 'RSID', 
            'Round1_prelim', 'Round2_prelim', 'Round3_prelim', 
            'Ruzzo2019', 'SF', 'SFARIscore_2019q1', 'SF_called_by', 
            'SF_comment', 'Sanders2015', 'Stessman2017', 'UW', 'UW_called_by', 
            'VEP_amino_acids', 'VEP_canonical', 'VEP_codons', 
            'VEP_consequence', 'VEP_exon', 'VEP_impact', 'VEP_intron', 
            'Xregion', 'aa_len', 'aa_pos', 'allele_frac', 
            'allelic_requirement', 'asd', 'asd_score', 'biotype', 
            'brain_expression', 'cdna_len', 'cdna_pos', 'cds_len', 
            'cds_pos', 'clinvar_allele_origin', 'clinvar_clnsig', 
            'clinvar_clnsig_includedVar', 'clinvar_conflicting_clnsig', 
            'clinvar_consequence', 'clinvar_gene', 'clinvar_hgvs', 
            'clinvar_prevalence', 'clinvar_review', 'clinvar_source', 
            'clinvar_suspectReasonCode', 'clinvar_trait', 
            'clinvar_trait_includedVar', 'clinvar_vartype', 'coding_var', 
            'cohort_freq_comment_perFamily(ALT_DP>1)', 
            'cohort_freq_variant_perFamily(ALT_DP>1)', 'consistent_with_PG', 
            'dbNSFP_Aloft_Confidence', 
            'dbNSFP_Aloft_Fraction_transcripts_affected', 
            'dbNSFP_Aloft_pred', 'dbNSFP_Aloft_prob_Dominant', 
            'dbNSFP_Aloft_prob_Recessive', 'dbNSFP_Aloft_prob_Tolerant', 
            'dbNSFP_CADD_phred', 'dbNSFP_ExAC_AF', 'dbNSFP_ExAC_Adj_AF', 
            'dbNSFP_ExAC_nonTCGA_AF', 'dbNSFP_ExAC_nonTCGA_Adj_AF', 
            'dbNSFP_ExAC_nonpsych_AF', 'dbNSFP_ExAC_nonpsych_Adj_AF', 
            'dbNSFP_HGVSc_ANNOVAR', 'dbNSFP_HGVSp_ANNOVAR', 'dbNSFP_MVP', 
            'dbNSFP_M_CAP_pred', 'dbNSFP_MetaLR_pred', 'dbNSFP_MetaSVM_pred', 
            'dbNSFP_Polyphen2_HDIV_pred', 'dbNSFP_Polyphen2_HVAR_pred', 
            'dbNSFP_REVEL', 'dbNSFP_SIFT4G_pred', 'dbNSFP_SIFT_pred', 
            'dbNSFP_aaalt', 'dbNSFP_aapos', 'dbNSFP_aaref', 
            'dbNSFP_cds_strand', 'dbNSFP_gnomAD_exomes_AF', 
            'dbNSFP_gnomAD_exomes_AFR_AF', 'dbNSFP_gnomAD_exomes_AMR_AF', 
            'dbNSFP_gnomAD_exomes_ASJ_AF', 'dbNSFP_gnomAD_exomes_EAS_AF', 
            'dbNSFP_gnomAD_exomes_FIN_AF', 'dbNSFP_gnomAD_exomes_NFE_AF', 
            'dbNSFP_gnomAD_exomes_POPMAX_AF', 'dbNSFP_gnomAD_exomes_SAS_AF', 
            'dbNSFP_gnomAD_exomes_controls_AF', 
            'dbNSFP_gnomAD_exomes_controls_AFR_AF', 
            'dbNSFP_gnomAD_exomes_controls_AMR_AF', 
            'dbNSFP_gnomAD_exomes_controls_ASJ_AF', 
            'dbNSFP_gnomAD_exomes_controls_EAS_AF', 
            'dbNSFP_gnomAD_exomes_controls_FIN_AF', 
            'dbNSFP_gnomAD_exomes_controls_NFE_AF', 
            'dbNSFP_gnomAD_exomes_controls_POPMAX_AF', 
            'dbNSFP_gnomAD_exomes_controls_SAS_AF', 
            'dbNSFP_gnomAD_exomes_flag', 
            'dbNSFP_gnomAD_genomes_AF', 
            'dbNSFP_gnomAD_genomes_AFR_AF', 
            'dbNSFP_gnomAD_genomes_AMR_AF', 
            'dbNSFP_gnomAD_genomes_ASJ_AF', 'dbNSFP_gnomAD_genomes_EAS_AF', 
            'dbNSFP_gnomAD_genomes_FIN_AF', 'dbNSFP_gnomAD_genomes_NFE_AF', 
            'dbNSFP_gnomAD_genomes_POPMAX_AF', 
            'dbNSFP_gnomAD_genomes_controls_AF', 
            'dbNSFP_gnomAD_genomes_controls_AFR_AF', 
            'dbNSFP_gnomAD_genomes_controls_AMR_AF', 
            'dbNSFP_gnomAD_genomes_controls_ASJ_AF', 
            'dbNSFP_gnomAD_genomes_controls_EAS_AF', 
            'dbNSFP_gnomAD_genomes_controls_FIN_AF', 
            'dbNSFP_gnomAD_genomes_controls_NFE_AF', 
            'dbNSFP_gnomAD_genomes_controls_POPMAX_AF', 
            'dbNSFP_gnomAD_genomes_flag', 
            'difference_with_MZ_twin', 'distance', 'dmg_miss_wMPC_MVP', 
            'dv_alt', 'dv_child_gq', 'dv_child_gt', 'dv_confirmed', 
            'dv_confirmed_binary', 'dv_father_gq', 'dv_father_gt', 
            'dv_mother_gq', 'dv_mother_gt', 'dv_qual', 'dv_ref', 
            'effect_cat', 'effect_cat_PG', 'exon/intron', 'father', 
            'feature', 'gene_blacklisted', 'gene_symbol', 'geneid', 
            'hgvsc', 'hgvsp', 'high_confidence', 'igv', 'impact', 
            'inheritance', 'lab_validation', 'mother', 'mutation_consequence', 
            'mutation_type', 'mutation_type_extended', 'n_callers', 
            'n_centers', 'numResiduesFromEnd', 'num_rare_LGD', 
            'num_rare_SparkLGD', 'observed_counts_vartype_perFamily(ALT_DP>1)', 
            'order_reason', 'organ_specificity_list', 'pLI', 
            'pg_transcript_effect', 'pg_transcript_errors', 
            'pg_transcript_hgvsc', 'pg_transcript_hgvsp', 'pg_transcript_id', 
            'pg_transcript_impact', 'posMultipleVariantsPerFamily', 
            'possibleMNV', 'postsynapticDensityProteins', 
            'protein_id_ensembl', 'role', 'sex', 'sfid', 'sparkGenes', 
            'spid_outliers', 'transcript_id_ensembl', 'transcript_id_refseq', 
            'twin_mz', 'variant_id', 'warnings_errors', 'watchGeneList', 
            'zygosity'
        ]
        for name in cleanup_names:
            if name in vprops:
                del vprops[name]
        keys = list(vprops.keys())
        for key in keys:
            if key == "":
                del vprops[key]
            elif "\\" in key:
                del vprops[key]

    def _build_variants_df(self, variants):
        records = []
        for v in variants:
            for aa in v.alt_alleles:
                vprops = copy.deepcopy(aa.attributes)
                if "transmission_type" in vprops:
                    del vprops["transmission_type"]
                vprops["fvuid"] = v.fvuid
                vprops["effect_gene_genes"] = \
                    ",".join(vprops["effect_gene_genes"])
                vprops["effect_gene_types"] = \
                    ",".join(vprops["effect_gene_types"])
                vprops["effect_details_transcript_ids"] = \
                    ",".join(vprops["effect_details_transcript_ids"])
                vprops["effect_details_details"] = \
                    ",".join(vprops["effect_details_details"])

                self._cleanup_allele_attributes(vprops)

                vprops["chromosome"] = aa.chromosome
                vprops["position"] = aa.position
                vprops["reference"] = aa.reference
                vprops["alternative"] = aa.alternative
                vprops["family_id"] = aa.family_id
                vprops["cshl_location"] = aa.details.cshl_location
                vprops["cshl_variant"] = aa.details.cshl_variant

                records.append(vprops)

        df = pd.DataFrame.from_records(records)

        if len(df) > 1:
            df = df.sort_values(
                by=["chromosome", "position", "fvuid", "allele_index"])
            df = df.reset_index(drop=True)
            print("variants df:", df.head())
            with io.StringIO() as inout:
                df.to_csv(inout, sep="\t", index=False)
                inout.seek(0, io.SEEK_SET)

                df = pd.read_csv(inout, sep="\t")

        return df

    def _variants_diff(self, variants_df, expected_df):
        if len(variants_df) == len(expected_df) == 0:
            print("match")
            return

        if len(variants_df) > 0 and len(expected_df) > 0:
            if all(variants_df.index != expected_df.index):
                print("DIFF: indecies differ")
            if all(variants_df.columns != expected_df.columns):
                print("DIFF: columns differ")

            diff_df = variants_df.compare(
                expected_df, keep_shape=False, align_axis=0)
            print("diff:", diff_df.head())

    def _execute_test_case(self, expectation, case, study):
        study_id = expectation["study"]

        params = case["params"]
        params = self._parse_frequency(params)
        params = self._parse_genomic_scores(params)

        expected = case["expected"]
        case_name = case["name"]
        print(f"\ttesting {case_name}: {params}")

        start = time.time()

        if study is None:
            test_result = TestResult(
                expectation=expectation,
                case=case,
                test_for="count",
                params=params,
                expected=expected,
                result=None,
            )
            test_result.message = f"can't find study {study_id}",
            test_result.status = TestStatus.ERROR
            return test_result

        variants = list(study.query_variants(**params))
        df = self._build_variants_df(variants)
        variants_filename = self._build_case_expections_filename(case)
        assert os.path.exists(variants_filename)

        print("variants file size:", os.path.getsize(variants_filename))
        try:
            expect_df = pd.read_csv(variants_filename, sep="\t")
        except pd.errors.EmptyDataError:
            expect_df = pd.DataFrame({})
            assert len(expect_df) == 0

        print("expect_df:", expect_df.head())
        # df.to_csv(variants_filename, sep="\t", index=False)
        test_result = self._variants_diff(df, expect_df)

        assert "count" in expected
        count = expected["count"]

        variants_count = sum(1 for v in variants)
        test_result = TestResult(
            expectation=expectation,
            case=case,
            test_for="count",
            params=params,
            expected=expected,
            result=variants_count
        )

        if variants_count == count:
            test_result.status = TestStatus.PASSED
            test_result.message = "PASSED"
            print("\t\t\tPASSED")
        else:
            test_result.status = TestStatus.FAIL
            test_result.message = f"FAILED: expected {count}; " \
                f"got {variants_count} variants"
            print(
                f"\t\t\t{test_result.message}")
        end = time.time()
        test_result.time = (end-start)
        return test_result

    def _validate_genotype_browser(self, expectation):
        study_id = expectation["study"]
        cases = expectation["cases"]
        target = expectation["target"]
        name = expectation["name"]

        test_suite = TestSuite(study_id, target, name)
        self.test_suites.append(test_suite)

        study = self.gpf_instance.get_genotype_data(study_id)

        for case in cases:
            test_result = self._execute_test_case(expectation, case, study)
            test_suite.append(test_result)

    def run(self):
        target = self.expectations["target"]
        study_id = self.expectations["study"]
        name = self.expectations["name"]
        assert target == "genotype_browser"

        print("==================================================")
        print(f"validating {study_id} {target}: {name}")
        self._validate_genotype_browser(self.expectations)

    # def run_validations(self):
    #     print("VALIDATION START")
    #     for expectation in self.expectations:
    #         target = expectation["target"]
    #         study_id = expectation["study"]
    #         name = expectation["name"]
    #         assert target == "genotype_browser"

    #         print("==================================================")
    #         print(f"validating {study_id} {target}: {name}")
    #         if target == "genotype_browser":
    #             self._validate_genotype_browser(expectation)
    #         elif target == "families_report":
    #             self._validate_families_report(expectation)
    #         elif target == "denovo_reports":
    #             self._validate_denovo_reports(expectation)
    #         else:
    #             pass

    #     print("VALIDATION END")
    #     print(
    #         f"passed: {self.passed_case_count}; "
    #         f"failed: {self.failed_case_count}")
    #     with open("results.xml", "w") as outfile:
    #         outfile.write(self.get_xml().decode("utf8"))


class MainRunner:

    def __init__(self, gpf_instance, outfilename):
        self.gpf_instance = gpf_instance
        self.outfilename = outfilename
        self.runners = []

    @staticmethod
    def collect_expectations(expectations):
        for filename in glob.glob(expectations):
            assert os.path.exists(filename), filename
            with open(filename, "r") as infile:
                res = yaml.load(infile, Loader=yaml.FullLoader)
                for expectation in res:
                    expectation["file"] = filename
                    for case in expectation["cases"]:
                        print(case)
                        assert "name" in case
                        case_id = case["name"]\
                            .replace(" ", "_")\
                            .replace("-", "_")\
                            .replace("<", "") \
                            .replace(">", "") \
                            .replace("=", "") \
                            .replace("%", "") \
                            .replace("(", "") \
                            .replace(")", "") \
                            .lower()
                        case["id"] = case_id
                    seen = set()
                    for case in expectation["cases"]:
                        assert case["id"] not in seen
                        seen.add(case["id"])
                        print(case["id"])

                    yield expectation

    def make_validation_runner(self, expectations):
        target = expectations["target"]
        if target == "genotype_browser":
            return GenotypeBrowserRunner(expectations, self.gpf_instance)
        else:
            raise NotImplementedError(
                f"not supported expectations target: {target}")

    @staticmethod
    def store_junit_results(runners, outfilename):
        root = Element("testsuites")
        for runner in runners:
            for suite in runner.test_suites:
                root.append(suite.to_xml_element())
        with open(outfilename, "w") as outfile:
            outfile.write(
                tostring(root, encoding="utf8", method="xml").decode("utf8"))

    def main(self, expectations_iterator):
        self.runners = []
        for expectations in expectations_iterator:
            runner = self.make_validation_runner(expectations)
            runner.run()
            self.runners.append(runner)

        self.store_junit_results(self.runners, self.outfilename)

    def _counter(self, status):
        count = 0
        for runner in self.runners:
            count += runner._counter(status)
        return count

    @property
    def failed_case_count(self):
        return self._counter(TestStatus.FAIL)

    @property
    def errors_case_count(self):
        return self._counter(TestStatus.ERROR)

    @property
    def passed_case_count(self):
        return self._counter(TestStatus.PASSED)

    def summary(self):
        print(100*"=")
        print(
            f"FAILED: {self.failed_case_count}; "
            f"ERRORS: {self.errors_case_count}; "
            f"PASSED: {self.passed_case_count}; "
            f"TOTAL: {self.failed_case_count + self.passed_case_count}")
        print(100*"=")


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "expectations", type=str,
        help='expectation filename or glob'
    )
    parser.add_argument('--verbose', '-V', action='count', default=0)
    parser.add_argument(
        "--output", "-o", type=str, default="validation-result.xml",
        help="output filename for JUnit result XML file")

    args = parser.parse_args(argv)
    if args.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif args.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)
    logging.getLogger("impala").setLevel(logging.WARNING)

    gpf_instance = GPFInstance()
    main_runner = MainRunner(gpf_instance, args.output)

    expectations_iterator = MainRunner.collect_expectations(args.expectations)
    main_runner.main(expectations_iterator)
    main_runner.summary()


if __name__ == "__main__":
    main(sys.argv[1:])
