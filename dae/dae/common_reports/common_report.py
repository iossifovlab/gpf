import time
import logging

from dae.variants.attributes import Role

from dae.common_reports.family_report import FamiliesReport
from dae.common_reports.people_counter import PeopleReport
from dae.common_reports.denovo_report import DenovoReport


logger = logging.getLogger(__name__)


class CommonReport(object):
    def __init__(self, json):
        self.id = json["id"]
        self.people_report = PeopleReport(json["people_report"])
        self.families_report = FamiliesReport(json["families_report"])
        self.denovo_report = DenovoReport(json.get("denovo_report"))
        self.study_name = json["study_name"]
        self.phenotype = json["phenotype"]
        self.study_type = json["study_type"]
        self.study_year = json["study_year"]
        self.pub_med = json["pub_med"]
        self.families = json["families"]
        self.number_of_probands = json["number_of_probands"]
        self.number_of_siblings = json["number_of_siblings"]
        self.denovo = json["denovo"]
        self.transmitted = json["transmitted"]
        self.study_description = json["study_description"]

    @staticmethod
    def from_genotype_study(genotype_data_study):
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

        people_report = PeopleReport.from_families(
            genotype_data_study.families,
            families_report_collections
        )

        elapsed = time.time() - start
        logger.info(
            f"COMMON REPORTS family report " f"build in {elapsed:.2f} sec")

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
            f"COMMON REPORTS denovo report " f"build in {elapsed:.2f} sec")

        person_sets_config = \
            genotype_data_study.config.person_set_collections

        assert person_sets_config.selected_person_set_collections \
            is not None, config

        collection = genotype_data_study.get_person_set_collection(
            person_sets_config.selected_person_set_collections[0]
        )
        phenotype = list()
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

    def to_dict(self):
        return {
            "id": self.id,
            "people_report": self.people_report.to_dict(),
            "families_report": self.families_report.to_dict(),
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
