import argparse
import os
import io
import sys
import glob
import logging
import copy
import enum
from typing import Any, Iterator, Optional, cast


from xml.etree.ElementTree import Element, tostring

import yaml
import pandas as pd
import numpy as np

from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.utils.regions import Region
from dae.studies.study import GenotypeData
from dae.variants.family_variant import FamilyVariant, FamilyAllele

logger = logging.getLogger("gpf_validation_runner")


class TestStatus(enum.Enum):
    NOTSET = 0
    PASSED = 1
    FAIL = 2
    ERROR = 4


class TestResult:
    """Encapsulate the result of a test."""

    def __init__(
        self,
        expectation: Optional[dict[str, Any]] = None,
        case: Optional[dict[str, Any]] = None,
        test_for: Optional[str] = None,
        params: Optional[dict[str, Any]] = None,
        result: Optional[str] = None
    ) -> None:

        self.expectation = expectation
        self.case = case
        self.test_for = test_for
        self.params = params
        self.status = TestStatus.NOTSET
        self.result = result
        self.message: Optional[str] = None
        self.time: Optional[float] = None

    def __str__(self) -> str:
        assert self.case is not None
        case_name = self.case["name"]
        assert self.expectation is not None
        filename = self.expectation["file"]

        out = f"{filename}: {case_name}: {self.test_for} "
        if self.status == TestStatus.PASSED:
            out += "PASSED"
        elif self.status == TestStatus.FAIL:
            out += f"FAILED: {self.message},"
        elif self.status == TestStatus.ERROR:
            out += f"ERROR: {self.message},"
        return out

    def to_xml_element(self) -> Element:
        """Convert to an XML element."""
        assert self.case is not None
        assert self.expectation is not None
        assert self.params is not None
        assert self.test_for is not None

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
    """A collection of tests."""

    def __init__(self, study: str, target: str, name: str) -> None:
        self.study = study
        self.name = name
        self.target = target
        self.cases: list[TestResult] = []

    def append(self, case: TestResult) -> None:
        self.cases.append(case)

    def to_xml_element(self) -> Element:
        """Convert to an XML element."""
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
    """The base class for test runners."""

    def __init__(
        self, expectations: dict[str, Any], gpf_instance: GPFInstance
    ) -> None:

        self.expectations = expectations
        self.gpf_instance = gpf_instance
        # self.failed_case_count = 0
        # self.passed_case_count = 0
        self.test_suites: list[TestSuite] = []
        assert self.gpf_instance

    def _counter(self, status: TestStatus) -> int:
        count = 0
        for suite in self.test_suites:
            for case in suite.cases:
                if case.status == status:
                    count += 1
        return count

    @property
    def failed_case_count(self) -> int:
        return self._counter(TestStatus.FAIL)

    @property
    def passed_case_count(self) -> int:
        return self._counter(TestStatus.PASSED)

    @property
    def error_case_count(self) -> int:
        return self._counter(TestStatus.ERROR)

    # def get_xml(self):
    #     root = Element("testsuites")
    #     for suite in self.test_suites:
    #         root.append(suite.to_xml_element())
    #     return tostring(root, encoding="utf8", method="xml")


class BaseGenotypeBrowserRunner(AbstractRunner):
    """Base class for Genotype Browser Runners."""

    def _parse_frequency(
        self, params: dict[str, Any]
    ) -> dict[str, Any]:
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

    def _parse_genomic_scores(
        self, params: dict[str, Any]
    ) -> dict[str, Any]:
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

    def _parse_regions(
        self, params: dict[str, Any]
    ) -> dict[str, Any]:
        if params is None:
            return None

        if "regions" in params:
            regions = []
            for region in params["regions"]:
                reg = Region.from_str(region)
                regions.append(reg)
            params["regions"] = regions
        return params


class GenotypeBrowserRunner(BaseGenotypeBrowserRunner):
    """Run Genotype Browser tests."""

    def __init__(
        self, expectations: dict[str, Any],
        gpf_instance: GPFInstance,
        detailed_reporting: bool, skip_columns: set
    ) -> None:
        self.detailed_reporting = detailed_reporting
        self.skip_columns = set(skip_columns)

        super().__init__(expectations, gpf_instance)

    def _build_case_expections_filename(
        self, case: dict[str, Any],
        dirname: Optional[str] = None
    ) -> str:
        case_dirname, _ = os.path.splitext(self.expectations["file"])
        if dirname is not None:
            case_dirname = os.path.join(dirname, case_dirname)

        os.makedirs(case_dirname, exist_ok=True)

        return os.path.join(case_dirname, f"{case['id']}.tsv")

    def _checked_columns(self) -> set[str]:
        keep = {
            "af_allele_count",
            "af_allele_freq",
            "af_parents_called_count",
            "af_parents_called_percent",
            "allele_count",
            "allele_index",
            "alternative",
            "cadd_phred",
            "cadd_raw",
            "chrom",
            "chromosome",
            "cshl_location",
            "cshl_variant",
            "effect_details_details",
            "effect_details_transcript_ids",
            "effect_gene_genes",
            "effect_gene_types",
            "effect_type",
            "exome_gnomad_ac",
            "exome_gnomad_af",
            "exome_gnomad_af_percent",
            "exome_gnomad_an",
            "exome_gnomad_controls_ac",
            "exome_gnomad_controls_af",
            "exome_gnomad_controls_af_percent",
            "exome_gnomad_controls_an",
            "exome_gnomad_non_neuro_ac",
            "exome_gnomad_non_neuro_af",
            "exome_gnomad_non_neuro_af_percent",
            "exome_gnomad_non_neuro_an",
            "exome_gnomad_v2_1_1_ac",
            "exome_gnomad_v2_1_1_af_percent",
            "exome_gnomad_v2_1_1_an",
            "exome_gnomad_v2_1_1_controls_ac",
            "exome_gnomad_v2_1_1_controls_af_percent",
            "exome_gnomad_v2_1_1_controls_an",
            "exome_gnomad_v2_1_1_non_neuro_ac",
            "exome_gnomad_v2_1_1_non_neuro_af_percent",
            "exome_gnomad_v2_1_1_non_neuro_an",
            "family_id",
            "fitcons2_e067",
            "fitcons2_e068",
            "fitcons2_e069",
            "fitcons2_e070",
            "fitcons2_e071",
            "fitcons2_e072",
            "fitcons2_e073",
            "fitcons2_e074",
            "fitcons2_e081",
            "fitcons2_e082",
            "fitcons_i6_merged",
            "fvuid",
            "genome_gnomad_ac",
            "genome_gnomad_af",
            "genome_gnomad_af_percent",
            "genome_gnomad_an",
            "genome_gnomad_controls_ac",
            "genome_gnomad_controls_af",
            "genome_gnomad_controls_af_percent",
            "genome_gnomad_controls_an",
            "genome_gnomad_non_neuro_ac",
            "genome_gnomad_non_neuro_af",
            "genome_gnomad_non_neuro_af_percent",
            "genome_gnomad_non_neuro_an",
            "genome_gnomad_v2_1_1_ac",
            "genome_gnomad_v2_1_1_af_percent",
            "genome_gnomad_v2_1_1_an",
            "genome_gnomad_v2_1_1_controls_ac",
            "genome_gnomad_v2_1_1_controls_af_percent",
            "genome_gnomad_v2_1_1_controls_an",
            "genome_gnomad_v2_1_1_non_neuro_ac",
            "genome_gnomad_v2_1_1_non_neuro_af_percent",
            "genome_gnomad_v2_1_1_non_neuro_an",
            "genome_gnomad_v3_ac",
            "genome_gnomad_v3_af_percent",
            "genome_gnomad_v3_an",
            "linsight",
            "mpc",
            "phastcons100",
            "phastcons100way",
            "phastcons20way",
            "phastcons30way",
            "phastcons46_placentals",
            "phastcons46_primates",
            "phastcons46_vertebrates",
            "phastcons7way",
            "phylop100",
            "phylop100way",
            "phylop20way",
            "phylop30way",
            "phylop46_placentals",
            "phylop46_primates",
            "phylop46_vertebrates",
            "phylop7way",
            "position",
            "reference",
            "ssc_freq",
            "study_name",
            "study_phenotype"
        }
        if self.skip_columns:
            keep = keep.difference(self.skip_columns)

        return keep

    def _cleanup_variant_columns(self, columns: set[str]) -> set[str]:
        keep = self._checked_columns()
        return columns.intersection(keep)

    def _cleanup_allele_attributes(
        self, vprops: dict[str, Any]
    ) -> None:
        keep = self._checked_columns()
        keys = list(vprops.keys())
        for key in keys:
            if key not in keep:
                del vprops[key]

    def _build_variants_df(
        self, variants: list[FamilyVariant]
    ) -> pd.DataFrame:
        records = []
        for v in variants:
            for aa in v.alt_alleles:
                fa = cast(FamilyAllele, aa)
                vprops = aa.attributes

                if "transmission_type" in vprops:
                    del vprops["transmission_type"]
                if "af_allele_count" not in vprops:
                    vprops["af_allele_count"] = ""
                    vprops["af_allele_freq"] = ""
                    vprops["af_parents_called_count"] = ""
                    vprops["af_parents_called_percent"] = ""

                vprops["fvuid"] = v.fvuid
                if fa.effects is None:
                    vprops["effect_type"] = None
                    vprops["effect_gene_genes"] = None
                    vprops["effect_gene_types"] = None
                    vprops["effect_details_transcript_ids"] = None
                    vprops["effect_details_details"] = None
                else:
                    vprops["effect_type"] = fa.effects.worst_effect
                    vprops["effect_gene_genes"] = \
                        ",".join([str(g.symbol) for g in fa.effects.genes])
                    vprops["effect_gene_types"] = \
                        ",".join([str(g.effect) for g in fa.effects.genes])

                    effect_details_transcripts = fa.effects.transcripts.keys()
                    vprops["effect_details_transcript_ids"] = \
                        ",".join(effect_details_transcripts)
                    effect_details_details = [
                        str(d) for d in fa.effects.transcripts.values()]
                    vprops["effect_details_details"] = \
                        ",".join(effect_details_details)

                self._cleanup_allele_attributes(vprops)

                vprops["chromosome"] = aa.chromosome
                vprops["position"] = aa.position
                vprops["reference"] = aa.reference
                vprops["alternative"] = aa.alternative
                vprops["family_id"] = fa.family_id
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

    # pylint: disable=too-many-branches
    def _variants_diff(
        self, variants_df: pd.DataFrame,
        expected_df: pd.DataFrame
    ) -> Optional[str]:
        if len(variants_df) == 0 and len(expected_df) == 0:
            return None
        try:
            assert set(variants_df.columns) == set(expected_df.columns), (
                variants_df.columns, expected_df.columns)

            assert len(variants_df) == len(expected_df), \
                f"expected {len(expected_df)} variants, " \
                f"got {len(variants_df)}"

            variants_df = variants_df.sort_index().sort_index(axis=1)
            expected_df = expected_df.sort_index().sort_index(axis=1)

            pd.testing.assert_frame_equal(
                variants_df.sort_index(axis=1), expected_df.sort_index(axis=1)
            )
        except AssertionError as ex:
            return self._error_reporter(ex, variants_df, expected_df)
        except Exception:  # pylint: disable=broad-except
            logger.error(
                "unexpected exception whild running tests", exc_info=True)

        return None

    def _error_reporter(
        self, ex: AssertionError,
        variants_df: pd.DataFrame,
        expected_df: pd.DataFrame
    ) -> str:
        with io.StringIO() as out:
            if not self.detailed_reporting:
                print("expected:\n", expected_df.head(), file=out)
                print("actual:\n", variants_df.head(), file=out)
                print(ex, file=out)
                return out.getvalue()

            expected_columns = self._cleanup_variant_columns(
                set(expected_df.columns))
            variants_columns = self._cleanup_variant_columns(
                set(variants_df.columns))
            diff1 = expected_columns.difference(variants_columns)
            if diff1:
                print(
                    "columns expected but not found in variants:",
                    diff1, file=out)
            diff2 = variants_columns.difference(expected_columns)
            if diff2:
                print(
                    "columns found in variants but not expected:",
                    diff2, file=out)
            if diff1 or diff2:
                return out.getvalue()

            if all(expected_df.columns != expected_df.columns):
                print(
                    "columns are in different order: ",
                    "expected>", expected_df.columns,
                    "variants>", variants_df.columns,
                    file=out)
                return out.getvalue()

            if len(expected_df) != len(variants_df):
                print(
                    "different number of variants: ",
                    "expected>", len(expected_df),
                    "variants>", len(variants_df),
                    file=out)
                return out.getvalue()

            differences = (expected_df != variants_df).stack()
            last_printed_idx = -1
            for idxs, has_diff in differences.items():
                if not has_diff:
                    continue

                idx, col_name = cast(tuple[int, str], idxs)
                expected = expected_df[col_name][idx]
                result = variants_df[col_name][idx]

                if isinstance(expected, np.float64):
                    if np.isclose(expected, result):
                        continue

                if isinstance(expected, str):
                    if expected == result:
                        continue
                if isinstance(expected, np.float64) and \
                        np.isnan(expected) and np.isnan(result):
                    continue

                if last_printed_idx != idx:
                    last_printed_idx = idx
                    print(
                        f"Differences in variant #{idx} "
                        f"{expected_df['chromosome'][idx]} "
                        f"{expected_df['position'][idx]} "
                        f"{expected_df['reference'][idx]}->"
                        f"{expected_df['alternative'][idx]} "
                        f"{expected_df['cshl_variant'][idx]} ",
                        file=out
                    )
                print(
                    f"\t{col_name}:\n"
                    f"\t\tExpected: > {expected_df[col_name][idx]}\n"
                    f"\t\tResult:   > {variants_df[col_name][idx]}",
                    file=out
                )
            return out.getvalue()

    def _execute_variants_test_case(
        self, case: dict[str, Any],
        params: dict[str, Any],
        variants: list[FamilyVariant]
    ) -> Optional[TestResult]:
        variants_df = self._build_variants_df(variants)
        variants_filename = self._build_case_expections_filename(case)
        if not os.path.exists(variants_filename):
            return None

        try:
            expected_df = pd.read_csv(variants_filename, sep="\t")
            if len(expected_df) == 0:
                if len(variants_df) == 0:
                    # match
                    pass
                else:
                    # mismatch
                    expected_df = pd.DataFrame({})
            else:
                to_remove = set(self.skip_columns)
                columns = [
                    c for c in expected_df.columns if c not in to_remove]
                expected_df = expected_df[columns]

        except pd.errors.EmptyDataError:
            expected_df = pd.DataFrame({})
            assert len(expected_df) == 0

        # df.to_csv(variants_filename, sep="\t", index=False)

        expected_columns = self._cleanup_variant_columns(
            set(expected_df.columns))
        variants_columns = self._cleanup_variant_columns(
            set(variants_df.columns))

        variants_df = variants_df[list(variants_columns)]
        expected_df = expected_df[list(expected_columns)]

        diff = self._variants_diff(variants_df, expected_df)

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
            test_result.message = \
                f"\n" \
                f"reading expected variants from {variants_filename};\n" \
                f"{diff}"

        return test_result

    def _execute_count_test_case(
        self, case: dict[str, Any],
        params: dict[str, Any],
        variants: list[FamilyVariant]
    ) -> TestResult:
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
            test_result.message = \
                f"FAILED: expected {count}; " \
                f"got {variants_count} variants"
        return test_result

    def _case_query_params(self, case: dict[str, Any]) -> dict[str, Any]:
        if case["params"] is None:
            return {}

        params = cast(dict[str, Any], copy.deepcopy(case["params"]))
        params = self._parse_frequency(params)
        params = self._parse_genomic_scores(params)
        params = self._parse_regions(params)

        return params

    def _execute_test_case(
        self, case: dict[str, Any],
        study: GenotypeData
    ) -> tuple[TestResult, Optional[TestResult]]:
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
                test_result.message = (f"can't find study {study_id}",)
                test_result.status = TestStatus.ERROR
                return (test_result, )

            variants = list(study.query_variants(**params))

            count_result = self._execute_count_test_case(
                case, params, variants)

            variants_result = self._execute_variants_test_case(
                case, params, variants)

            return (count_result, variants_result)
        except Exception as ex:  # pylint: disable=broad-except
            logger.debug(
                "unexpected error %s: %s", study_id, ex, exc_info=True)
            test_result = TestResult(
                expectation=self.expectations,
                case=case,
                test_for="count/variants",
                params=params,
                result=None,
            )
            test_result.message = f"unexpected error {study_id}: {ex}"
            test_result.status = TestStatus.ERROR
            return (test_result, None)

    def _validate_genotype_browser(self) -> None:
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

    def store_results(self, dirname: str) -> None:
        """Store results."""
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

    def run(self) -> None:
        """Run tests."""
        target = self.expectations["target"]
        study_id = self.expectations["study"]
        name = self.expectations["name"]
        assert target == "genotype_browser"

        print("==================================================")
        print(f"validating {study_id} {target}: {name}")
        self._validate_genotype_browser()


class MainRunner:
    """Main runner."""

    def __init__(
            self, gpf_instance: GPFInstance, outfilename: str,
            detailed_reporting: bool,
            skip_columns: list[Any]) -> None:
        self.gpf_instance = gpf_instance
        self.outfilename = outfilename
        self.runners: list[AbstractRunner] = []
        self.detailed_reporting = detailed_reporting
        self.skip_columns = set(skip_columns)

    @staticmethod
    def collect_expectations(
        expectations: str
    ) -> Iterator[dict[str, Any]]:
        """Collect expectations."""
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

    def make_validation_runner(
        self, expectations: dict[str, Any]
    ) -> GenotypeBrowserRunner:
        """Create a validation runner."""
        target = expectations["target"]
        if target == "genotype_browser":
            return GenotypeBrowserRunner(
                expectations, self.gpf_instance,
                self.detailed_reporting, self.skip_columns
            )
        raise NotImplementedError(
            f"not supported expectations target: {target}")

    @staticmethod
    def store_junit_results(
        runners: list[AbstractRunner],
        outfilename: str
    ) -> None:
        """Store junit results."""
        root = Element("testsuites")
        for runner in runners:
            for suite in runner.test_suites:
                root.append(suite.to_xml_element())
        with open(outfilename, "w") as outfile:
            outfile.write(
                tostring(root, encoding="utf8", method="xml").decode("utf8"))

    def main(self, expectations_iterator: Iterator[Any]) -> None:
        """Entry point for this runner."""
        self.runners = []
        for expectations in expectations_iterator:
            runner = self.make_validation_runner(expectations)
            runner.run()
            self.runners.append(runner)

        self.store_junit_results(self.runners, self.outfilename)

    def store_results(
        self, expectations_iterator: Iterator[dict[str, Any]],
        dirname: str
    ) -> None:
        for expectations in expectations_iterator:
            runner = self.make_validation_runner(expectations)
            runner.store_results(dirname)

    def _counter(self, status: TestStatus) -> int:
        count = 0
        for runner in self.runners:
            # pylint: disable=protected-access
            count += runner._counter(status)
        return count

    @property
    def failed_case_count(self) -> int:
        return self._counter(TestStatus.FAIL)

    @property
    def errors_case_count(self) -> int:
        return self._counter(TestStatus.ERROR)

    @property
    def passed_case_count(self) -> int:
        return self._counter(TestStatus.PASSED)

    def summary(self) -> None:
        """Print a summary of the test results."""
        print(100 * "=")
        print(
            f"FAILED: {self.failed_case_count}; "
            f"ERRORS: {self.errors_case_count}; "
            f"PASSED: {self.passed_case_count}; "
            f"TOTAL: {self.failed_case_count + self.passed_case_count}")
        print(100 * "=")


def main(argv: Optional[list[str]] = None) -> None:
    """Entry point for the runner script."""
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "expectations", type=str,
        help="expectation filename or glob"
    )
    parser.add_argument(
        "--output", "-o", type=str, default="validation-result.xml",
        help="output filename for JUnit result XML file")

    parser.add_argument(
        "--store-results", type=str,
        help="a directory where to store genotype variants into TSV files")

    parser.add_argument(
        "--detailed-reporting", "--dr",
        action="store_true", default=False,
        help="Use detailed logging of differences per variant per column")
    parser.add_argument(
        "--skip-columns", "--sk",
        type=str, default=None,
        help="Comma separated list of columns to skip when comparing with "
        "expectations")

    VerbosityConfiguration.set_arguments(parser)

    args = parser.parse_args(argv)
    if args.skip_columns is None:
        skip_columns = []
    else:
        skip_columns = [c.strip() for c in args.skip_columns.split(",")]
    print("skipping columns:", skip_columns)

    VerbosityConfiguration.set(args)

    gpf_instance = GPFInstance.build()
    main_runner = MainRunner(
        gpf_instance, args.output, args.detailed_reporting, skip_columns)

    expectations_iterator = MainRunner.collect_expectations(args.expectations)

    if args.store_results is not None:
        os.makedirs(args.store_results, exist_ok=True)
        main_runner.store_results(expectations_iterator, args.store_results)
    else:
        main_runner.main(expectations_iterator)
        main_runner.summary()


if __name__ == "__main__":
    main(sys.argv[1:])
