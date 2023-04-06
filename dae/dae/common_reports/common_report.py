from __future__ import annotations

import os
import time
import logging
import json
from typing import Optional

from dae.variants.attributes import Role

from dae.common_reports.family_report import FamiliesReport
from dae.common_reports.people_counter import PeopleReport
from dae.common_reports.denovo_report import DenovoReport


logger = logging.getLogger(__name__)


class CommonReport:
    """Class representing a common report JSON."""

    def __init__(self, data):
        self.study_id = data["id"]
        self.people_report = PeopleReport(data["people_report"])
        self.families_report = FamiliesReport(data["families_report"])
        self.denovo_report = DenovoReport(data.get("denovo_report"))
        self.study_name = data["study_name"]
        self.phenotype = data["phenotype"]
        self.study_type = data["study_type"]
        self.study_year = data["study_year"]
        self.pub_med = data["pub_med"]
        self.families = data["families"]
        self.number_of_probands = data["number_of_probands"]
        self.number_of_siblings = data["number_of_siblings"]
        self.denovo = data["denovo"]
        self.transmitted = data["transmitted"]
        self.study_description = data["study_description"]

    @staticmethod
    def build_report(genotype_data_study):
        """Generate common report JSON from genotpye data study."""
        config = genotype_data_study.config.common_report

        assert config.enabled, genotype_data_study.study_id

        start = time.time()

        if config.selected_person_set_collections.family_report:
            families_report_collections = [
                genotype_data_study.person_set_collections[collection_id]
                for collection_id in
                config.selected_person_set_collections.family_report
            ]
        else:
            families_report_collections = \
                genotype_data_study.person_set_collections.values()

        families_report = FamiliesReport.from_genotype_study(
            genotype_data_study,
            families_report_collections,
        )

        people_report = PeopleReport.from_person_set_collections(
            families_report_collections
        )

        elapsed = time.time() - start
        logger.info(
            "COMMON REPORTS family report build in %.2f sec", elapsed
        )

        start = time.time()

        if config.selected_person_set_collections.denovo_report:
            denovo_report_collections = [
                genotype_data_study.person_set_collections[collection_id]
                for collection_id in
                config.selected_person_set_collections.denovo_report
            ]
        else:
            denovo_report_collections = \
                genotype_data_study.person_set_collections.values()

        denovo_report = DenovoReport.from_genotype_study(
            genotype_data_study,
            denovo_report_collections
        )
        elapsed = time.time() - start
        logger.info(
            "COMMON REPORTS denovo report build in %.2f sec", elapsed
        )

        person_sets_config = \
            genotype_data_study.config.person_set_collections

        assert person_sets_config.selected_person_set_collections \
            is not None, config

        collection = genotype_data_study.get_person_set_collection(
            person_sets_config.selected_person_set_collections[0]
        )
        phenotype = []
        for person_set in collection.person_sets.values():
            if len(person_set.persons) > 0:
                phenotype += person_set.values

        study_type = (
            ",".join(genotype_data_study.study_type)
            if genotype_data_study.study_type
            else None
        )

        number_of_probands = 0
        number_of_siblings = 0
        for family in genotype_data_study.families.values():
            for person in family.members_in_order:
                if person.role == Role.prb:
                    number_of_probands += 1
                if person.role == Role.sib:
                    number_of_siblings += 1

        return CommonReport({
            "id": genotype_data_study.study_id,
            "people_report": people_report.to_dict(),
            "families_report": families_report.to_dict(full=True),
            "denovo_report": (
                denovo_report.to_dict()
                if not denovo_report.is_empty()
                else None
            ),
            "study_name": genotype_data_study.name,
            "phenotype": phenotype,
            "study_type": study_type,
            "study_year": genotype_data_study.year,
            "pub_med": genotype_data_study.pub_med,
            "families": len(genotype_data_study.families.values()),
            "number_of_probands": number_of_probands,
            "number_of_siblings": number_of_siblings,
            "denovo": genotype_data_study.has_denovo,
            "transmitted": genotype_data_study.has_transmitted,
            "study_description": genotype_data_study.description,
        })

    def to_dict(self, full=False):
        return {
            "id": self.study_id,
            "people_report": self.people_report.to_dict(),
            "families_report": self.families_report.to_dict(full=full),
            "denovo_report": (
                self.denovo_report.to_dict()
                if not self.denovo_report.is_empty()
                else None
            ),
            "study_name": self.study_name,
            "phenotype": self.phenotype,
            "study_type": self.study_type,
            "study_year": self.study_year,
            "pub_med": self.pub_med,
            "families": self.families,
            "number_of_probands": self.number_of_probands,
            "number_of_siblings": self.number_of_siblings,
            "denovo": self.denovo,
            "transmitted": self.transmitted,
            "study_description": self.study_description,
        }

    def save(self, report_filename: str) -> None:
        """Save common report into a file."""
        if not os.path.exists(os.path.dirname(report_filename)):
            os.makedirs(os.path.dirname(report_filename))
        with open(report_filename, "w+", encoding="utf8") as crf:
            json.dump(self.to_dict(full=True), crf)

    @staticmethod
    def load(report_filename: str) -> Optional[CommonReport]:
        """Load a common report from a file.

        If file does not exists returns None.
        """
        if not os.path.exists(report_filename):
            return None
        with open(report_filename, "r", encoding="utf-8") as crf:
            cr_json = json.load(crf)

        return CommonReport(cr_json)

    @staticmethod
    def build_and_save(study, force=False):
        """Build a common report for a study, saves it and returns the report.

        If the common reports are disabled for the study, the function skips
        building the report and returns None.

        If the report already exists the default behavior is to skip building
        the report. You can force building the report by
        passing `force=True` to the function.
        """
        if not study.config.common_report.enabled:
            return None
        report_filename = study.config.common_report.file_path
        try:
            if os.path.exists(report_filename) and not force:
                return CommonReport.load(report_filename)
        except Exception:  # pylint: disable=broad-except
            logger.warning(
                "unable to load common report for %s", study.study_id,
                exc_info=True)
        report = CommonReport.build_report(study)
        report.save(report_filename)
        return report
