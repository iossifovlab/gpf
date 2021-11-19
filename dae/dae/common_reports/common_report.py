import time
import logging

from collections import OrderedDict

from dae.variants.attributes import Role

from dae.common_reports.family_report import FamiliesReport
from dae.common_reports.people_counter import PeopleReport
from dae.common_reports.denovo_report import DenovoReport


logger = logging.getLogger(__name__)


class CommonReport(object):
    def __init__(self, genotype_data_study):
        config = genotype_data_study.config.common_report
        effect_groups = config.effect_groups
        effect_types = config.effect_types

        assert config.enabled, genotype_data_study.study_id

        self.genotype_data_study = genotype_data_study
        self.id = genotype_data_study.study_id

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

        self.families_report = FamiliesReport(
            genotype_data_study.families,
            families_report_collections,
            config.draw_all_families,
            config.families_count_show_id,
        )

        self.people_report = PeopleReport(
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

        self.denovo_report = DenovoReport(
            genotype_data_study,
            effect_groups,
            effect_types,
            denovo_report_collections
        )
        elapsed = time.time() - start
        logger.info(
            f"COMMON REPORTS denovo report " f"build in {elapsed:.2f} sec")

        self.study_name = genotype_data_study.name
        self.phenotype = self._get_phenotype()
        self.study_type = (
            ",".join(genotype_data_study.study_type)
            if genotype_data_study.study_type
            else None
        )
        self.study_year = genotype_data_study.year
        self.pub_med = genotype_data_study.pub_med

        self.families = len(genotype_data_study.families.values())
        self.number_of_probands = self._get_number_of_people_with_role(
            Role.prb
        )
        self.number_of_siblings = self._get_number_of_people_with_role(
            Role.sib
        )
        self.denovo = genotype_data_study.has_denovo
        self.transmitted = genotype_data_study.has_transmitted
        self.study_description = genotype_data_study.description

    def to_dict(self):
        return OrderedDict(
            [
                ("id", self.id),
                ("people_report", self.people_report.to_dict()),
                ("families_report", self.families_report.to_dict()),
                (
                    "denovo_report",
                    (
                        self.denovo_report.to_dict()
                        if not self.denovo_report.is_empty()
                        else None
                    ),
                ),
                ("study_name", self.study_name),
                ("phenotype", self.phenotype),
                ("study_type", self.study_type),
                ("study_year", self.study_year),
                ("pub_med", self.pub_med),
                ("families", self.families),
                ("number_of_probands", self.number_of_probands),
                ("number_of_siblings", self.number_of_siblings),
                ("denovo", self.denovo),
                ("transmitted", self.transmitted),
                ("study_description", self.study_description),
            ]
        )

    def _get_phenotype(self):
        config = self.genotype_data_study.config.person_set_collections
        assert config.selected_person_set_collections is not None, config

        collection = self.genotype_data_study.get_person_set_collection(
            config.selected_person_set_collections[0]
        )
        result = list()
        for person_set in collection.person_sets.values():
            if len(person_set.persons) > 0:
                result += person_set.values
        return result

    def _get_number_of_people_with_role(self, role):
        counter = 0
        for family in self.genotype_data_study.families.values():
            for person in family.members_in_order:
                if person.role == role:
                    counter += 1
        return counter
