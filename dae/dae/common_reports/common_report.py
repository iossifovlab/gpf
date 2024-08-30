from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, cast

from dae.common_reports.denovo_report import DenovoReport
from dae.common_reports.family_report import FamiliesReport
from dae.common_reports.people_counter import PeopleReport

logger = logging.getLogger(__name__)


class CommonReport:
    """Class representing a common report JSON."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.study_id = data["id"]
        self.people_report = PeopleReport(data["people_report"])
        self.families_report = FamiliesReport(data["families_report"])
        self.denovo_report = DenovoReport(
            cast(dict[str, Any], data.get("denovo_report")))
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

    def to_dict(self, full: bool = False) -> dict[str, Any]:
        return {
            "id": self.study_id,
            "people_report": self.people_report.to_dict(),
            "families_report": self.families_report.to_dict(full=full),
            "denovo_report": (
                self.denovo_report.to_dict()
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
    def load(report_filename: str) -> CommonReport | None:
        """Load a common report from a file.

        If file does not exists returns None.
        """
        if not os.path.exists(report_filename):
            return None
        with open(report_filename, "r", encoding="utf-8") as crf:
            cr_json = json.load(crf)

        return CommonReport(cr_json)
