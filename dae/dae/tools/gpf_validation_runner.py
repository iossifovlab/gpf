import argparse
import os
import sys
import glob
import yaml
import time
import logging

from xml.etree.ElementTree import Element, tostring

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.variants.attributes import Sex


class TestResult:
    def __init__(
            self, study, file, target, test_for, case_number,
            params, expected, result, time=0.0):
        self.study = study
        self.file = file
        self.target = target
        self.test_for = test_for
        self.case_number = case_number
        self.params = params
        self.expected = expected
        self.success = False
        self.time = time
        self.result = result

    def __str__(self):
        out = f"{self.study} {self.test_for} test {self.case_number} "
        if self.success:
            out += "PASSED"
        else:
            out += f"expected {self.expected},"
        return out

    def to_xml_element(self):
        testcase = Element("testcase")
        name = f"Case {self.case_number}:{self.test_for}"
        for param, value in self.params.items():
            if isinstance(value, list):
                value_str = ",".join([str(v) for v in value])
            else:
                value_str = str(value)
            name += f"|{param}[{value_str}]"
        testcase.set("name", str(name))
        testcase.set("time", str(self.time))
        testcase.set("file", self.file)
        testcase.set(
            "classname",
            f"{self.study}:{self.target}:{self.test_for}"
        )
        if not self.success:
            failure = Element("failure")
            failure.set(
                "message",
                f"Expected {self.expected}, Got {self.result}")
            testcase.append(failure)
        return testcase


class TestSuite:
    def __init__(self, study, target, name):
        self.study = study
        self.name = name
        self.target = target
        self.results = list()

    def append(self, result):
        self.results.append(result)

    def to_xml_element(self):
        testsuite = Element("testsuite")
        testsuite.set("name", f"{self.study} {self.target}: {self.name}")
        testsuite.set("tests", str(len(self.results)))
        failures = \
            len(list(filter(lambda x: x.success is False, self.results)))
        testsuite.set("failures", str(failures))
        for result in self.results:
            testsuite.append(result.to_xml_element())
        return testsuite


class Runner:

    def __init__(
            self, 
            expectations):

        self.expectations = expectations
        self.instance = GPFInstance()
        self.failed_case_count = 0
        self.passed_case_count = 0
        self.test_suites = []
        assert self.instance

    def _collect_expectations(self):
        for filename in glob.glob(self.expectations):
            assert os.path.exists(filename), filename
            with open(filename, "r") as infile:
                res = yaml.load(infile, Loader=yaml.FullLoader)
                for expectation in res:
                    expectation["file"] = filename
                    yield expectation

    def _validate_families_report(self, expectation):
        study_id = expectation["study"]
        cases = expectation["cases"]
        file = expectation["file"]
        target = expectation["target"]

        test_suite = TestSuite(study_id, target)
        self.test_suites.append(test_suite)

        for case_number, case in enumerate(cases):
            start = time.time()
            params = case["params"]
            sex = None
            collection = params["collection_id"]
            value = params["collection_value"]
            if "sex" in params:
                sex = Sex.from_name(params["sex"])
            print("--------------------------------")
            print(f"Querying with params {params}")

            expected = case["expected"]

            if "count" in expected:
                count = expected["count"]

                facade = self.instance._common_report_facade
                persons = facade.query_person_counters(
                    study_id, collection, value, sex=sex
                )

                person_count = len(persons)

                test_result = TestResult(
                        study_id,
                        file,
                        target,
                        "count",
                        case_number,
                        params,
                        expected,
                        person_count
                )

                print(f"Expected {count} persons")
                if person_count == count:
                    test_result.success = True
                    print("PASSED")
                else:
                    test_result.success = False
                    print(f"Got: {person_count}")
                    self.failed_case_count += 1

                end = time.time()
                test_result.time = (end-start)
                test_suite.append(test_result)

    def _validate_denovo_reports(self, expectation):
        study_id = expectation["study"]
        cases = expectation["cases"]
        file = expectation["file"]
        target = expectation["target"]

        test_suite = TestSuite(study_id, target)

        for case_number, case in enumerate(cases):
            start = time.time()
            params = case["params"]
            collection = params["collection_id"]
            value = params["collection_value"]
            effect_type = params["effect_type"]
            print("--------------------------------")
            print(f"Querying with params {params}")

            expected = case["expected"]

            if "count" in expected:
                count = expected["count"]

                facade = self.instance._common_report_facade
                results = facade.query_denovo_reports(
                    study_id, collection, value, effect_type
                )

                person_count = results["number_of_observed_events"]

                test_result = TestResult(
                        study_id,
                        file,
                        target,
                        "count",
                        case_number,
                        params,
                        expected,
                        person_count
                )

                print(f"Expected {count} persons")
                if person_count == count:
                    test_result.success = True
                    print("PASSED")
                else:
                    test_result.success = False
                    print(f"Got: {person_count}")
                    self.failed_case_count += 1
                end = time.time()
                test_result.time = (end-start)
                test_suite.append(test_result)

        self.test_suites.append(test_suite)

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

    def _validate_genotype_browser(self, expectation):
        study_id = expectation["study"]
        cases = expectation["cases"]
        file = expectation["file"]
        target = expectation["target"]
        name = expectation["name"]

        test_suite = TestSuite(study_id, target, name)
        self.test_suites.append(test_suite)

        study = self.instance.get_genotype_data(study_id)
        if study is None:
            test_result = TestResult(
                    study_id,
                    file,
                    target,
                    "study",
                    0,
                    {"study_id": study_id},
                    study_id,
                    None
            )
            test_result.success = False
            test_suite.append(test_result)
            self.failed_case_count += 1
            self.test_suites.append(test_suite)
            return

        for case_number, case in enumerate(cases):
            start = time.time()
            params = case["params"]
            params = self._parse_frequency(params)
            params = self._parse_genomic_scores(params)

            expected = case["expected"]
            case_name = case["name"]
            print(f"\ttesting {case_name}: {params}")

            variants = study.query_variants(**params)

            if "count" in expected:
                count = expected["count"]
                variants_count = sum(1 for v in variants)
                test_result = TestResult(
                        study_id,
                        file,
                        target,
                        "count",
                        case_number,
                        params,
                        expected,
                        variants_count
                )

                if variants_count == count:
                    test_result.success = True
                    self.passed_case_count += 1
                    print("\t\t\tPASSED")
                else:
                    test_result.success = False
                    print(
                        f"\t\t\tFAILED: expected {count}; "
                        f"got {variants_count} variants")
                    self.failed_case_count += 1
                end = time.time()
                test_result.time = (end-start)
                test_suite.append(test_result)

    def get_xml(self):
        root = Element("testsuites")
        for suite in self.test_suites:
            root.append(suite.to_xml_element())
        return tostring(root, encoding="utf8", method="xml")

    def run_validations(self):
        self.failed_case_count = 0
        expectations = self._collect_expectations()
        print("VALIDATION START")
        for expectation in expectations:
            target = expectation["target"]
            study_id = expectation["study"]
            name = expectation["name"]

            print("==================================================")
            print(f"validating {study_id} {target}: {name}")
            if target == "genotype_browser":
                self._validate_genotype_browser(expectation)
            elif target == "families_report":
                self._validate_families_report(expectation)
            elif target == "denovo_reports":
                self._validate_denovo_reports(expectation)
            else:
                pass

        print("VALIDATION END")
        print(
            f"passed: {self.passed_case_count}; "
            f"failed: {self.failed_case_count}")
        with open("results.xml", "w") as outfile:
            outfile.write(self.get_xml().decode("utf8"))


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "expectations", type=str,
        help='expectation filename or glob'
    )
    parser.add_argument('--verbose', '-V', action='count', default=0)

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

    runner = Runner(args.expectations)
    assert runner is not None
    runner.run_validations()


if __name__ == "__main__":
    main(sys.argv[1:])
