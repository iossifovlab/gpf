import argparse
import os
import io
import sys
import glob
import yaml
import logging
import copy
import enum
import pandas as pd

from xml.etree.ElementTree import Element, tostring

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.utils.regions import Region


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
            result=None):

        self.expectation = expectation
        self.case = case
        self.test_for = test_for
        self.params = params
        self.status = TestStatus.NOTSET
        self.result = result
        self.message = None
        self.time = None

    def __str__(self):
        case_name = self.case["name"]
        filename = self.expectation["file"]

        out = f"{filename}: {case_name}: {self.test_for} "
        if self.status == TestStatus.PASSED:
            out += "PASSED"
        elif self.status == TestStatus.FAIL:
            out += f"FAILED: {self.message},"
        elif self.status == TestStatus.ERROR:
            out += f"ERROR: {self.message},"
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
                f"{self.message}")
            testcase.append(failure)
        elif self.status == TestStatus.ERROR:
            error = Element("error")
            error.set(
                "message",
                f"{self.message}")
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
            len(list(
                filter(lambda x: x.status == TestStatus.FAIL, self.cases)))
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
        if params is None:
            return params
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
        if params is None:
            return params
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

    def _parse_regions(self, params):
        if params is None:
            return None

        if "regions" in params:
            regions = []
            for region in params["regions"]:
                r = Region.from_str(region)
                regions.append(r)
            params["regions"] = regions
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

    def _build_case_expections_filename(self, case, dirname=None):
        case_dirname, _ = os.path.splitext(self.expectations["file"])
        if dirname is not None:
            case_dirname = os.path.join(dirname, case_dirname)

        os.makedirs(case_dirname, exist_ok=True)

        return os.path.join(case_dirname, f"{case['id']}.tsv")

    @staticmethod
    def _cleanup_allele_attributes(vprops):
        keep = {
            'af_allele_count',
            'af_allele_freq',
            'af_parents_called_count',
            'af_parents_called_percent',
            'allele_count',
            'allele_index',
            'alternative',
            'bucket_index',
            'cadd_phred',
            'cadd_raw',
            'chrom',
            'chromosome',
            'cshl_location',
            'cshl_variant',
            'effect_details_details',
            'effect_details_transcript_ids',
            'effect_gene_genes',
            'effect_gene_types',
            'effect_type',
            'exome_gnomad_ac',
            'exome_gnomad_af',
            'exome_gnomad_af_percent',
            'exome_gnomad_an',
            'exome_gnomad_controls_ac',
            'exome_gnomad_controls_af',
            'exome_gnomad_controls_af_percent',
            'exome_gnomad_controls_an',
            'exome_gnomad_non_neuro_ac',
            'exome_gnomad_non_neuro_af',
            'exome_gnomad_non_neuro_af_percent',
            'exome_gnomad_non_neuro_an',
            'exome_gnomad_v2_1_1_ac',
            'exome_gnomad_v2_1_1_af_percent',
            'exome_gnomad_v2_1_1_an',
            'exome_gnomad_v2_1_1_controls_ac',
            'exome_gnomad_v2_1_1_controls_af_percent',
            'exome_gnomad_v2_1_1_controls_an',
            'exome_gnomad_v2_1_1_non_neuro_ac',
            'exome_gnomad_v2_1_1_non_neuro_af_percent',
            'exome_gnomad_v2_1_1_non_neuro_an',
            'family_id',
            'family_variant_index',
            'fitcons2_e067',
            'fitcons2_e068',
            'fitcons2_e069',
            'fitcons2_e070',
            'fitcons2_e071',
            'fitcons2_e072',
            'fitcons2_e073',
            'fitcons2_e074',
            'fitcons2_e081',
            'fitcons2_e082',
            'fitcons_i6_merged',
            'fvuid',
            'genome_gnomad_ac',
            'genome_gnomad_af',
            'genome_gnomad_af_percent',
            'genome_gnomad_an',
            'genome_gnomad_controls_ac',
            'genome_gnomad_controls_af',
            'genome_gnomad_controls_af_percent',
            'genome_gnomad_controls_an',
            'genome_gnomad_non_neuro_ac',
            'genome_gnomad_non_neuro_af',
            'genome_gnomad_non_neuro_af_percent',
            'genome_gnomad_non_neuro_an',
            'genome_gnomad_v2_1_1_ac',
            'genome_gnomad_v2_1_1_af_percent',
            'genome_gnomad_v2_1_1_an',
            'genome_gnomad_v2_1_1_controls_ac',
            'genome_gnomad_v2_1_1_controls_af_percent',
            'genome_gnomad_v2_1_1_controls_an',
            'genome_gnomad_v2_1_1_non_neuro_ac',
            'genome_gnomad_v2_1_1_non_neuro_af_percent',
            'genome_gnomad_v2_1_1_non_neuro_an',
            'genome_gnomad_v3_ac',
            'genome_gnomad_v3_af_percent',
            'genome_gnomad_v3_an',
            'linsight',
            'mpc',
            'phastcons100',
            'phastcons100way',
            'phastcons20way',
            'phastcons30way',
            'phastcons46_placentals',
            'phastcons46_primates',
            'phastcons46_vertebrates',
            'phastcons7way',
            'phylop100',
            'phylop100way',
            'phylop20way',
            'phylop30way',
            'phylop46_placentals',
            'phylop46_primates',
            'phylop46_vertebrates',
            'phylop7way',
            'position',
            'reference',
            'ssc_freq',
            'study_name',
            'study_phenotype'}

        keys = list(vprops.keys())
        for key in keys:
            if key not in keep:
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

                effect_details = filter(
                    lambda x: x is not None,
                    vprops["effect_details_transcript_ids"])
                vprops["effect_details_transcript_ids"] = \
                    ",".join(effect_details)
                effect_details = filter(
                    lambda x: x is not None,
                    vprops["effect_details_details"])
                vprops["effect_details_details"] = \
                    ",".join(effect_details)

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

        if len(df) > 0:
            df = df.sort_values(
                by=[
                    "chromosome", "position", "family_id",
                    "fvuid", "allele_index"
                ])
            df = df.reset_index(drop=True)
            with io.StringIO() as inout:
                df.to_csv(inout, sep="\t", index=False)
                inout.seek(0, io.SEEK_SET)

                df = pd.read_csv(inout, sep="\t")

        return df

    def _variants_diff(self, variants_df, expected_df):

        try:
            assert set(variants_df.columns) == set(expected_df.columns), (
                variants_df.columns, expected_df.columns)

            pd.testing.assert_frame_equal(variants_df, expected_df)

        except AssertionError as ex:
            with io.StringIO() as out:
                print("expected:\n", expected_df.head(), file=out)
                print("actual:\n", variants_df.head(), file=out)
                print(ex, file=out)
                return out.getvalue()

        return None

    def _execute_variants_test_case(self, case, params, variants):
        df = self._build_variants_df(variants)
        variants_filename = self._build_case_expections_filename(case)
        if not os.path.exists(variants_filename):
            return None

        try:
            expect_df = pd.read_csv(variants_filename, sep="\t")
        except pd.errors.EmptyDataError:
            expect_df = pd.DataFrame({})
            assert len(expect_df) == 0

        # df.to_csv(variants_filename, sep="\t", index=False)
        diff = self._variants_diff(df, expect_df)

        test_result = TestResult(
            expectation=self.expectations,
            case=case,
            test_for="variants",
            params=params,
        )

        if diff is None:
            test_result.status = TestStatus.PASSED
        else:
            test_result.status = TestStatus.FAIL
            test_result.message = f"\n" \
                f"reading expected variants from {variants_filename};\n" \
                f"{diff}"
        return test_result

    def _execute_count_test_case(self, case, params, variants):
        expected = case["expected"]

        assert "count" in expected
        count = expected["count"]

        variants_count = sum(1 for v in variants)
        test_result = TestResult(
            expectation=self.expectations,
            case=case,
            test_for="count",
            params=params,
        )

        if variants_count == count:
            test_result.status = TestStatus.PASSED
            test_result.message = "PASSED"
        else:
            test_result.status = TestStatus.FAIL
            test_result.message = f"FAILED: expected {count}; " \
                f"got {variants_count} variants"
        return test_result

    def _case_query_params(self, case):
        if case["params"] is None:
            return {}

        params = copy.deepcopy(case["params"])
        params = self._parse_frequency(params)
        params = self._parse_genomic_scores(params)
        params = self._parse_regions(params)

        return params

    def _execute_test_case(self, case, study):
        try:
            study_id = self.expectations["study"]
            params = self._case_query_params(case)

            if study is None:
                test_result = TestResult(
                    expectation=self.expectations,
                    case=case,
                    test_for="count",
                    params=params,
                    result=None,
                )
                test_result.message = f"can't find study {study_id}",
                test_result.status = TestStatus.ERROR
                return (test_result, )

            variants = list(study.query_variants(**params))

            count_result = self._execute_count_test_case(
                case, params, variants)

            variants_result = self._execute_variants_test_case(
                case, params, variants)

            return (count_result, variants_result)
        except Exception as ex:
            test_result = TestResult(
                expectation=self.expectations,
                case=case,
                test_for="count/variants",
                params=params,
                result=None,
            )
            test_result.message = f"unexpected error {study_id}: {ex}",
            test_result.status = TestStatus.ERROR
            return (test_result, )

    def _validate_genotype_browser(self):
        study_id = self.expectations["study"]
        cases = self.expectations["cases"]
        target = self.expectations["target"]
        name = self.expectations["name"]

        test_suite = TestSuite(study_id, target, name)
        self.test_suites.append(test_suite)

        study = self.gpf_instance.get_genotype_data(study_id)

        for case in cases:
            for test_result in self._execute_test_case(case, study):
                if test_result is None:
                    continue
                print("\t", test_result)
                test_suite.append(test_result)

    def store_results(self, dirname):
        study_id = self.expectations["study"]
        cases = self.expectations["cases"]
        target = self.expectations["target"]
        name = self.expectations["name"]

        test_suite = TestSuite(study_id, target, name)
        self.test_suites.append(test_suite)

        study = self.gpf_instance.get_genotype_data(study_id)
        for case in cases:
            params = self._case_query_params(case)
            variants = list(study.query_variants(**params))
            df = self._build_variants_df(variants)
            variants_filename = \
                self._build_case_expections_filename(case, dirname)
            print(f"stroring to: {variants_filename}")
            df.to_csv(variants_filename, index=False, sep="\t")

    def run(self):
        target = self.expectations["target"]
        study_id = self.expectations["study"]
        name = self.expectations["name"]
        assert target == "genotype_browser"

        print("==================================================")
        print(f"validating {study_id} {target}: {name}")
        self._validate_genotype_browser()


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
                            .replace("/", "_") \
                            .replace("+", "_p_") \
                            .replace("'", "") \
                            .lower()
                        case["id"] = case_id
                    seen = set()
                    for case in expectation["cases"]:
                        assert case["id"] not in seen
                        seen.add(case["id"])

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

    def store_results(self, expectations_iterator, dirname):
        for expectations in expectations_iterator:
            runner = self.make_validation_runner(expectations)
            runner.store_results(dirname)

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

    parser.add_argument(
        "--store-results", type=str,
        help="a directory where to store genotype variants into TSV files")

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

    if args.store_results is not None:
        os.makedirs(args.store_results, exist_ok=True)
        main_runner.store_results(expectations_iterator, args.store_results)
    else:
        main_runner.main(expectations_iterator)
        main_runner.summary()


if __name__ == "__main__":
    main(sys.argv[1:])
