# pylint: disable=too-many-lines
from __future__ import annotations

import logging
import math
import mimetypes
import os
from abc import ABC, abstractmethod
from collections.abc import Generator, Iterable, Sequence
from functools import cached_property
from itertools import chain, islice
from pathlib import Path
from typing import Any, cast

import duckdb
import pandas as pd

from dae.common_reports.common_report import CommonReport
from dae.common_reports.family_report import FamiliesReport
from dae.common_reports.people_counter import PeopleReport
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.family import Person
from dae.pedigrees.loader import FamiliesLoader
from dae.person_sets.person_sets import (
    PersonSetCollection,
    PersonSetCollectionConfig,
    parse_person_set_collections_study_config,
)
from dae.pheno.browser import PhenoBrowser
from dae.pheno.common import IMPORT_METADATA_TABLE, ImportManifest, MeasureType
from dae.pheno.db import PhenoDb
from dae.utils.helpers import isnan
from dae.variants.attributes import Role, Sex, Status

logger = logging.getLogger(__name__)


def get_pheno_db_dir(dae_config: dict | None) -> str:
    """Return the directory where phenotype data configurations are located."""
    if dae_config is not None:
        if (
            dae_config.get("phenotype_data") is None
            or dae_config["phenotype_data"]["dir"] is None
        ):
            pheno_data_dir = os.path.join(dae_config["conf_dir"], "pheno")
        else:
            pheno_data_dir = dae_config["phenotype_data"]["dir"]
    else:
        pheno_data_dir = os.path.join(os.environ.get("DAE_DB_DIR", ""), "pheno")

    return pheno_data_dir


def get_pheno_browser_images_dir(dae_config: dict | None = None) -> Path:
    """Get images directory for pheno DB."""
    if dae_config is None:
        pheno_data_dir = get_pheno_db_dir(dae_config)
        return Path(pheno_data_dir, "images")
    images_dir = dae_config.get("phenotype_images")
    if images_dir is not None:
        return Path(images_dir)

    cache_dir = dae_config.get("cache_path")
    if cache_dir is None:
        images_path = Path(get_pheno_db_dir(dae_config), "images")
    else:
        images_path = Path(cache_dir, "images")

    return images_path


class Instrument:
    """
    Instrument object represents phenotype instruments.

    Common fields are:

    * `instrument_name`

    * `measures` -- dictionary of all measures in the instrument
    """

    def __init__(self, name: str) -> None:
        self.instrument_name = name
        self.measures: dict[str, Measure] = {}

    def __repr__(self) -> str:
        return f"Instrument({self.instrument_name}, {len(self.measures)})"


class Measure:
    """
    Measure objects represent phenotype measures.

    Common fields are:

    * `instrument_name`

    * `measure_name`

    * `measure_id` - formed by `instrument_name`.`measure_name`

    * `measure_type` - one of 'continuous', 'ordinal', 'categorical'

    * `description`

    * `min_value` - for 'continuous' and 'ordinal' measures

    * `max_value` - for 'continuous' and 'ordinal' measures

    * `values_domain` - string that represents the values

    """

    def __init__(self, measure_id: str, name: str) -> None:
        self.measure_id = measure_id
        self.name: str = name
        self.measure_name: str = name
        self.measure_type: MeasureType = MeasureType.other
        self.values_domain: str | None = None
        self.instrument_name: str | None = None
        self.description: str | None = None
        self.default_filter = None
        self.min_value = None
        self.max_value = None

    def __repr__(self) -> str:
        return (
            f"Measure({self.measure_id}, "
            f"{self.measure_type}, {self.values_domain})"
        )

    @property
    def domain(self) -> Sequence[str | float]:
        """Return measure values domain."""
        domain_list: Sequence[str | float] = []
        if self.values_domain is not None:
            domain = (
                self.values_domain.replace("[", "")
                .replace("]", "")
                .replace(" ", "")
            )
            domain_list = domain.split(",")
            if self.measure_type in (
                MeasureType.continuous,
                MeasureType.ordinal,
            ):
                return list(map(float, domain_list))
        return domain_list

    @classmethod
    def from_record(cls, row: dict[str, Any]) -> Measure:
        """Create `Measure` object from pandas data frame row."""
        assert row["measure_type"] is not None

        mes = Measure(row["measure_id"], row["measure_name"])
        mes.instrument_name = row["instrument_name"]
        mes.measure_name = row["measure_name"]
        mes.measure_type = MeasureType(row["measure_type"])

        mes.description = row["description"]
        mes.default_filter = row["default_filter"]
        mes.values_domain = row.get("values_domain")
        mes.min_value = row.get("min_value")
        mes.max_value = row.get("max_value")

        return mes

    def to_json(self) -> dict[str, Any]:
        """Return measure description in JSON freindly format."""
        result: dict[str, Any] = {}

        result["measureName"] = self.measure_name
        result["measureId"] = self.measure_id
        result["instrumentName"] = self.instrument_name
        result["measureType"] = self.measure_type.name
        result["description"] = self.description
        result["defaultFilter"] = self.default_filter
        result["valuesDomain"] = self.values_domain
        result["minValue"] = \
            None if self.min_value is None or math.isnan(self.min_value) \
            else self.min_value
        result["maxValue"] = \
            None if self.max_value is None or math.isnan(self.max_value) \
            else self.max_value

        return result


class PhenotypeData(ABC):
    """Base class for all phenotype data studies and datasets."""

    def __init__(
        self,
        pheno_id: str,
        config: dict | None = None,
        cache_path: Path | None = None,
    ) -> None:
        self._pheno_id: str = pheno_id
        self.config = config if config is not None else {}
        self.name = self.config.get("name", pheno_id) \
            if self.config is not None \
            else pheno_id
        self._measures: dict[str, Measure] = {}
        self._instruments: dict[str, Instrument] = {}
        self._browser: PhenoBrowser | None = None
        self.cache_path = cache_path / self.pheno_id if cache_path else None

    @cached_property
    def families(self) -> FamiliesData:
        raise NotImplementedError

    @cached_property
    def person_set_collections(self) -> dict[str, PersonSetCollection]:
        raise NotImplementedError

    @property
    def pheno_id(self) -> str:
        return self._pheno_id

    def generate_import_manifests(
        self,
    ) -> list[ImportManifest]:
        """Collect all manifests in a phenotype data instance."""
        raise NotImplementedError

    @staticmethod
    def create_browser(
        pheno_data: PhenotypeData,
        *,
        read_only: bool = True,
    ) -> PhenoBrowser:
        """Load pheno browser from pheno configuration."""
        db_dir = pheno_data.cache_path or Path(pheno_data.config["conf_dir"])
        browser_dbfile = db_dir / f"{pheno_data.pheno_id}_browser.db"
        if not browser_dbfile.exists():
            if read_only:
                raise FileNotFoundError(
                    f"Browser DB file {browser_dbfile!s} not found.",
                )
            conn = duckdb.connect(browser_dbfile, read_only=False)
            conn.checkpoint()
            PhenoBrowser.create_browser_tables(conn)
            conn.close()
        browser = PhenoBrowser(
            str(browser_dbfile),
            read_only=read_only,
        )

        pheno_data.is_browser_outdated(browser)

        return browser

    def is_browser_outdated(self, browser: PhenoBrowser) -> bool:
        """Check if a rebuild is required according to manifests."""
        manifests = {
            manifest.import_config.id: manifest
            for manifest in ImportManifest.from_table(
                browser.connection, IMPORT_METADATA_TABLE,
            )
        }

        if len(manifests) == 0:
            logger.warning(
                "No manifests found in browser; either fresh or legacy",
            )
            return True

        pheno_data_manifests = {
            manifest.import_config.id: manifest
            for manifest in self.generate_import_manifests()
        }
        if len(set(manifests).symmetric_difference(pheno_data_manifests)) > 0:
            logger.warning("Manifest count mismatch between input and browser")
            return True

        is_outdated = False
        for pheno_id, pheno_manifest in pheno_data_manifests.items():
            browser_manifest = manifests[pheno_id]
            if browser_manifest.is_older_than(pheno_manifest):
                logger.warning("Browser manifest outdated for %s", pheno_id)
                is_outdated = True
        return is_outdated

    @property
    def browser(self) -> PhenoBrowser | None:
        """Get or create pheno browser for phenotype data."""
        if self._browser is None:
            try:
                self._browser = PhenotypeData.create_browser(self)
            except FileNotFoundError:
                logger.exception(
                    "Could not create browser for %s", self.pheno_id)
        return self._browser

    @property
    def measures(self) -> dict[str, Measure]:
        return self._measures

    @property
    def instruments(self) -> dict[str, Instrument]:
        return self._instruments

    def get_instruments(self) -> list[str]:
        return cast(list[str], self.instruments.keys())

    @abstractmethod
    def get_regressions(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def get_measures_info(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def get_persons_df(self) -> pd.DataFrame:
        pass

    def get_persons(self) -> dict[str, Person]:
        "Return individuals data from phenotype database."
        persons = {}
        df = self.get_persons_df()
        for row in df.to_dict("records"):
            person_id = row["person_id"]
            row["role"] = Role.from_value(row["role"])
            row["sex"] = Sex.from_value(row["sex"])
            row["status"] = Status.from_value(row["status"])

            person = Person(**row)  # type: ignore
            assert row["role"] in Role, f"{row['role']} not a valid role"
            assert row["sex"] in Sex, f"{row['sex']} not a valid sex"
            assert row["status"] in Status, \
                f"{row['status']} not a valid status"

            persons[person_id] = person
        return persons

    @abstractmethod
    def search_measures(
        self,
        instrument: str | None,
        search_term: str | None,
        page: int | None = None,
        sort_by: str | None = None,
        order_by: str | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """Yield measures in the DB according to filters."""

    @abstractmethod
    def count_measures(
        self,
        instrument: str | None,
        search_term: str | None,
        page: int | None = None,
    ) -> int:
        """Count measures in the DB according to filters."""

    def has_measure(self, measure_id: str) -> bool:
        """Check if phenotype DB contains a measure by ID."""
        return measure_id in self._measures

    def get_measure(self, measure_id: str) -> Measure:
        """Return a measure by measure_id."""
        assert measure_id in self._measures, measure_id
        return self._measures[measure_id]

    def get_image(self, image_path: str) -> tuple[bytes, str]:
        """Return binary image data with mimetype."""

        base_image_dir = Path(get_pheno_browser_images_dir())

        full_image_path = base_image_dir / image_path

        image_data = full_image_path.read_bytes()

        mimetype = mimetypes.guess_type(full_image_path)[0]

        if mimetype is None:
            raise ValueError(
                f"Cannot guess image mimetype of {full_image_path}",
            )

        return image_data, mimetype

    def get_measures(
        self,
        instrument_name: str | None = None,
        measure_type: MeasureType | None = None,
    ) -> dict[str, Measure]:
        """
        Return a dictionary of measures objects.

        `instrument_name` -- an instrument name which measures should be
        returned. If not specified all type of measures are returned.

        `measure_type` -- a type ('continuous', 'ordinal' or 'categorical')
        of measures that should be returned. If not specified all
        type of measures are returned.

        """
        result = {}

        instruments = self.instruments
        if instrument_name is not None:
            assert instrument_name in self.instruments
            instruments = {
                instrument_name: self.instruments[instrument_name],
            }

        if measure_type is not None:
            assert isinstance(measure_type, MeasureType)

        for instrument in instruments.values():
            for measure in instrument.measures.values():
                if measure_type is not None and \
                        measure.measure_type != measure_type:
                    continue
                result[measure.measure_id] = measure

        return result

    def get_measure_description(self, measure_id: str) -> dict[str, Any]:
        """Construct and return a measure description."""
        measure = self.measures[measure_id]

        out = {
            "instrument_name": measure.instrument_name,
            "measure_name": measure.measure_name,
            "measure_type": measure.measure_type.name,
            "values_domain": measure.domain,
        }
        if not (measure.min_value is None or math.isnan(measure.min_value)):
            out["min_value"] = measure.min_value
        if not (measure.max_value is None or math.isnan(measure.max_value)):
            out["max_value"] = measure.max_value
        return out

    def get_instrument_measures(self, instrument_name: str) -> list[str]:
        """Return measures for given instrument."""
        assert instrument_name in self.instruments
        instrument = self.instruments[instrument_name]
        return [
            m.measure_id for m in list(instrument.measures.values())
        ]

    @abstractmethod
    def get_people_measure_values(
        self,
        measure_ids: list[str],
        person_ids: list[str] | None = None,
        family_ids: list[str] | None = None,
        roles: list[Role] | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """
        Collect and format the values of the given measures in dict format.

        Yields a dict representing every row.

        `measure_ids` -- list of measure ids which values should be returned.

        `person_ids` -- list of person IDs to filter result. Only data for
        individuals with person_id in the list `person_ids` are returned.

        `family_ids` -- list of family IDs to filter result. Only data for
        individuals that are members of any of the specified `family_ids`
        are returned.

        `roles` -- list of roles of individuals to select measure value for.
        If not specified value for individuals in all roles are returned.
        """
        raise NotImplementedError

    def get_people_measure_values_df(
        self,
        measure_ids: list[str],
        person_ids: list[str] | None = None,
        family_ids: list[str] | None = None,
        roles: list[Role] | None = None,
    ) -> pd.DataFrame:
        """
        Collect and format the values of the given measures in a dataframe.

        `measure_ids` -- list of measure ids which values should be returned.

        `person_ids` -- list of person IDs to filter result. Only data for
        individuals with person_id in the list `person_ids` are returned.

        `family_ids` -- list of family IDs to filter result. Only data for
        individuals that are members of any of the specified `family_ids`
        are returned.

        `roles` -- list of roles of individuals to select measure value for.
        If not specified value for individuals in all roles are returned.
        """
        raise NotImplementedError

    @abstractmethod
    def get_children_ids(self, *, leaves: bool = True) -> list[str]:
        """Return all phenotype studies' ids in the group."""
        raise NotImplementedError

    @abstractmethod
    def _build_person_set_collection(
        self, psc_config: PersonSetCollectionConfig,
        families: FamiliesData,
    ) -> PersonSetCollection:
        pass

    def _build_person_set_collections(
        self,
        pheno_config: dict[str, Any] | None,
        families: FamiliesData,
    ) -> dict[str, PersonSetCollection]:
        if pheno_config is None:
            return {}
        if "person_set_collections" not in pheno_config:
            return {}
        pscs_config = parse_person_set_collections_study_config(pheno_config)
        return {
            psc_id: self._build_person_set_collection(psc_config, families)
            for psc_id, psc_config in pscs_config.items()
        }

    def get_person_set_collection(
        self, person_set_collection_id: str | None,
    ) -> PersonSetCollection | None:
        if person_set_collection_id is None:
            return None
        return self.person_set_collections.get(person_set_collection_id)

    def build_report(self) -> CommonReport:
        """Generate common report JSON from genotpye data study."""
        config = self.config["common_report"]

        assert config["enabled"], self.pheno_id

        selected = config.get("selected_person_set_collections")

        if selected and selected.get("family_report"):
            families_report_collections = [
                self.person_set_collections[collection_id]
                for collection_id in
                config["selected_person_set_collections"]["family_report"]
            ]
        else:
            families_report_collections = \
                list(self.person_set_collections.values())

        families_report = FamiliesReport.from_study(
            self,
            families_report_collections,
        )

        people_report = PeopleReport.from_person_set_collections(
            families_report_collections,
        )

        person_sets_config = self.config["person_set_collections"]

        collection = self.get_person_set_collection(
            person_sets_config["selected_person_set_collections"][0],
        )

        phenotype: list[str] = []
        assert collection is not None
        for person_set in collection.person_sets.values():
            if len(person_set.persons) > 0:
                phenotype += person_set.values  # noqa: PD011

        number_of_probands = 0
        number_of_siblings = 0
        for family in self.families.values():
            for person in family.members_in_order:
                if not family.member_is_child(person.person_id):
                    continue
                if person.role == Role.prb:
                    number_of_probands += 1
                if person.role == Role.sib:
                    number_of_siblings += 1

        return CommonReport({
            "id": self.pheno_id,
            "people_report": people_report.to_dict(),
            "families_report": families_report.to_dict(full=True),
            "denovo_report": None,
            "study_name": self.name,
            "phenotype": phenotype,
            "study_type": None,
            "study_year": None,
            "pub_med": None,
            "families": len(self.families.values()),
            "number_of_probands": number_of_probands,
            "number_of_siblings": number_of_siblings,
            "denovo": False,
            "transmitted": False,
            "study_description": "placeholder description",
        })

    def build_and_save(
        self,
        *,
        force: bool = False,
    ) -> CommonReport | None:
        """Build a common report for a study, saves it and returns the report.

        If the common reports are disabled for the study, the function skips
        building the report and returns None.

        If the report already exists the default behavior is to skip building
        the report. You can force building the report by
        passing `force=True` to the function.
        """
        if not self.config["common_report"]["enabled"]:
            return None
        report_filename = self.config["common_report"]["file_path"]
        try:
            if os.path.exists(report_filename) and not force:
                return CommonReport.load(report_filename)
        except Exception:  # noqa: BLE001
            logger.warning(
                "unable to load common report for %s", self.pheno_id,
                exc_info=True)
        report = self.build_report()
        report.save(report_filename)
        return report

    def get_common_report(self) -> CommonReport | None:
        """Return a study's common report."""
        if not self.config["common_report"]["enabled"]:
            return None

        report = CommonReport.load(self.config["common_report"]["file_path"])
        if report is None:
            report = self.build_and_save()
        return report


class PhenotypeStudy(PhenotypeData):
    """
    Main class for accessing phenotype database in DAE.

    To access the phenotype database create an instance of this class
    and call the method *load()*.

    Common fields of this class are:

    * `persons` -- list of all individuals in the database

    * `instruments` -- dictionary of all instruments

    * `measures` -- dictionary of all measures
    """

    def __init__(
        self,
        pheno_id: str,
        dbfile: str,
        config: dict | None = None,
        *,
        read_only: bool = True,
        cache_path: Path | None = None,
    ) -> None:
        super().__init__(pheno_id, config, cache_path=cache_path)

        self.db = PhenoDb(dbfile, read_only=read_only)
        df = self._get_measures_df()
        self._instruments = self._load_instruments(df)
        logger.info("phenotype study %s fully loaded", pheno_id)

    def generate_import_manifests(
        self,
    ) -> list[ImportManifest]:
        return [
            ImportManifest.from_table(
                self.db.connection, IMPORT_METADATA_TABLE,
            )[0],
        ]

    @cached_property
    def families(self) -> FamiliesData:
        return FamiliesLoader.build_families_data_from_pedigree(
            self.get_persons_df(),
        )

    @cached_property
    def person_set_collections(self) -> dict[str, PersonSetCollection]:
        return self._build_person_set_collections(
            self.config,
            self.families,
        )

    def _get_measures_df(
        self,
        instrument: str | None = None,
        measure_type: MeasureType | None = None,
    ) -> pd.DataFrame:
        """
        Return data frame containing measures information.

        `instrument` -- an instrument name which measures should be
        returned. If not specified all type of measures are returned.

        `measure_type` -- a type ('continuous', 'ordinal' or 'categorical')
        of measures that should be returned. If not specified all
        type of measures are returned.

        Each row in the returned data frame represents given measure.

        Columns in the returned data frame are: `measure_id`, `measure_name`,
        `instrument_name`, `description`, `stats`, `min_value`, `max_value`,
        `value_domain`, `has_probands`, `has_siblings`, `has_parents`,
        `default_filter`.
        """
        assert instrument is None or instrument in self.instruments
        assert measure_type is None or isinstance(measure_type, MeasureType)

        return self.db.get_measures_df(instrument, measure_type)

    def _load_instruments(self, df: pd.DataFrame) -> dict[str, Instrument]:
        instruments = {}

        instrument_names = list(df.instrument_name.unique())
        instrument_names = sorted(instrument_names)

        for instrument_name in instrument_names:
            instrument = Instrument(instrument_name)
            measures = {}
            measures_df = df[df.instrument_name == instrument_name]

            for row in measures_df.to_dict("records"):
                measure = Measure.from_record(row)
                measures[measure.measure_name] = measure
                self._measures[measure.measure_id] = measure
            instrument.measures = measures
            instruments[instrument.instrument_name] = instrument

        return instruments

    def get_people_measure_values(
        self,
        measure_ids: list[str],
        person_ids: list[str] | None = None,
        family_ids: list[str] | None = None,
        roles: list[Role] | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        yield from self.db.get_people_measure_values(
            measure_ids, person_ids, family_ids, roles,
        )

    def get_people_measure_values_df(
        self,
        measure_ids: list[str],
        person_ids: list[str] | None = None,
        family_ids: list[str] | None = None,
        roles: list[Role] | None = None,
    ) -> pd.DataFrame:
        return self.db.get_people_measure_values_df(
            measure_ids, person_ids, family_ids, roles,
        )

    def get_regressions(self) -> dict[str, Any]:
        if self.browser is None:
            return {}
        return self.browser.regression_display_names_with_ids

    def _get_pheno_images_base_url(self) -> str | None:
        if self.config is None:
            return None
        return cast(str | None, self.config.get("browser_images_url"))

    def get_measures_info(self) -> dict[str, Any]:
        if self.browser is None:
            return {
                "base_image_url": self._get_pheno_images_base_url(),
                "has_descriptions": {},
                "regression_names": {},
            }
        return {
            "base_image_url": self._get_pheno_images_base_url(),
            "has_descriptions": self.browser.has_descriptions,
            "regression_names": self.browser.regression_display_names,
        }

    def search_measures(
        self,
        instrument: str | None,
        search_term: str | None,
        page: int | None = None,
        sort_by: str | None = None,
        order_by: str | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        if self.browser is None:
            return
        measures = self.browser.search_measures(
            instrument,
            search_term,
            page,
            sort_by,
            order_by,
        )
        for measure in measures:
            if measure["values_domain"] is None:
                measure["values_domain"] = ""
            measure["measure_type"] = \
                cast(MeasureType, measure["measure_type"]).name

            measure["regressions"] = []
            for reg_id in self.browser.regression_ids:
                reg = {
                    "regression_id": reg_id,
                    "measure_id": measure["measure_id"],
                }

                if isnan(measure[f"{reg_id}_pvalue_regression_male"]):
                    measure[f"{reg_id}_pvalue_regression_male"] = "NaN"
                if isnan(measure[f"{reg_id}_pvalue_regression_female"]):
                    measure[f"{reg_id}_pvalue_regression_female"] = "NaN"

                reg["figure_regression"] = measure.pop(
                    f"{reg_id}_figure_regression",
                )
                reg["figure_regression_small"] = measure.pop(
                    f"{reg_id}_figure_regression_small",
                )
                reg["pvalue_regression_male"] = measure.pop(
                    f"{reg_id}_pvalue_regression_male",
                )
                reg["pvalue_regression_female"] = measure.pop(
                    f"{reg_id}_pvalue_regression_female",
                )
                measure["regressions"].append(reg)

            yield {
                "measure": measure,
            }

    def count_measures(
        self,
        instrument: str | None,
        search_term: str | None,
        page: int | None = None,
    ) -> int:
        if self.browser is None:
            return 0
        return self.browser.count_measures(
            instrument,
            search_term,
            page,
        )

    def get_children_ids(
        self, *, leaves: bool = True,  # noqa: ARG002
    ) -> list[str]:
        return [self.pheno_id]

    def get_persons_df(self) -> pd.DataFrame:
        return self.db.get_persons_df()

    def _build_person_set_collection(
        self,
        psc_config: PersonSetCollectionConfig,
        families: FamiliesData,
    ) -> PersonSetCollection:
        psc = PersonSetCollection.from_families(psc_config, self.families)
        for fpid, person in families.real_persons.items():
            person_set_value = psc.get_person_set_of_person(fpid)
            assert person_set_value is not None
            person.set_attr(psc.id, person_set_value.id)
        return psc


class PhenotypeGroup(PhenotypeData):
    """Represents a group of phenotype data studies or groups."""

    def __init__(
        self,
        pheno_id: str,
        config: dict | None,
        children: list[PhenotypeData],
        cache_path: Path | None = None,
    ) -> None:
        super().__init__(pheno_id, config, cache_path=cache_path)
        self.children = children
        instruments, measures = self._merge_instruments(
            [ph.instruments for ph in self.children],
        )
        self._instruments.update(instruments)

        self._measures.update(measures)

    def get_leaves(self) -> list[PhenotypeStudy]:
        """Return all phenotype studies in the group."""
        leaves = []
        for child in self.children:
            if child.config["type"] == "study":
                leaves.append(child)
            else:
                leaves.extend(cast(PhenotypeGroup, child).get_leaves())
        return leaves

    def generate_import_manifests(
        self,
    ) -> list[ImportManifest]:
        leaves = self.get_leaves()
        return [
            ImportManifest.from_table(
                leaf.db.connection, IMPORT_METADATA_TABLE,
            )[0]
            for leaf in leaves
        ]

    def get_children_ids(self, *, leaves: bool = True) -> list[str]:
        studies = self.get_leaves() if leaves else self.children
        return [data.pheno_id for data in studies]

    @staticmethod
    def _merge_instruments(
        phenos_instruments: Iterable[dict[str, Instrument]],
    ) -> tuple[dict[str, Instrument], dict[str, Measure]]:
        group_instruments: dict[str, Instrument] = {}
        group_measures: dict[str, Measure] = {}

        for pheno_instruments in phenos_instruments:
            for instrument_name, instrument in pheno_instruments.items():
                if instrument_name not in group_instruments:
                    group_instrument = Instrument(
                        instrument_name,
                    )
                else:
                    group_instrument = group_instruments[instrument_name]

                for name, measure in instrument.measures.items():
                    full_name = f"{instrument_name}.{name}"
                    if full_name in group_measures:
                        raise ValueError(
                            f"{full_name} measure duplication!",
                        )
                    group_instrument.measures[full_name] = measure
                    group_measures[full_name] = measure
                group_instruments[instrument_name] = group_instrument

        return group_instruments, group_measures

    def get_regressions(self) -> dict[str, Any]:
        res = {}
        for pheno in self.children:
            res.update(pheno.get_regressions())
        return res

    def get_measures_info(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "base_image_url": None,
            "has_descriptions": False,
            "regression_names": {},
        }
        for pheno in self.children:
            measures_info = pheno.get_measures_info()
            if result["base_image_url"] is None:
                result["base_image_url"] = measures_info["base_image_url"]
            result["has_descriptions"] = \
                result["has_descriptions"] or measures_info["has_descriptions"]
            cast(dict, result["regression_names"]).update(
                measures_info["regression_names"],
            )
        return result

    def search_measures(
        self,
        instrument: str | None,
        search_term: str | None,
        page: int | None = None,
        sort_by: str | None = None,
        order_by: str | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        generators = [
            pheno.search_measures(
                instrument,
                search_term,
                page,
                sort_by,
                order_by,
            )
            for pheno in self.children
        ]
        measures = islice(chain(*generators), 1001)
        yield from measures

    def count_measures(
        self,
        instrument: str | None,
        search_term: str | None,
        page: int | None = None,
    ) -> int:
        counts = [
            pheno.count_measures(
                instrument,
                search_term,
                page,
            )
            for pheno in self.children
        ]

        return sum(counts)

    def get_people_measure_values(
        self,
        measure_ids: list[str],
        person_ids: list[str] | None = None,
        family_ids: list[str] | None = None,
        roles: list[Role] | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        generators = []
        for child in self.children:
            measures_in_child = list(
                filter(child.has_measure, measure_ids))
            if len(measures_in_child) > 0:
                generators.append(child.get_people_measure_values(
                    measures_in_child,
                    person_ids,
                    family_ids,
                    roles,
                ))
        return cast(
            Generator[dict[str, Any], None, None],
            chain.from_iterable(generators),
        )

    def get_people_measure_values_df(
        self,
        measure_ids: list[str],
        person_ids: list[str] | None = None,
        family_ids: list[str] | None = None,
        roles: list[Role] | None = None,
    ) -> pd.DataFrame:
        measures_dfs: list[tuple[list[str], pd.DataFrame]] = []
        for child in self.children:
            measures_in_child = list(
                filter(child.has_measure, measure_ids))
            if len(measures_in_child) > 0:
                df = child.get_people_measure_values_df(
                    measures_in_child,
                    person_ids,
                    family_ids,
                    roles,
                )
                measures_dfs.append((measures_in_child, df))

        out_df = measures_dfs[0][1]
        for measures, df in measures_dfs[1:]:
            out_df = out_df.join(
                df.set_index("person_id")[measures],
                on="person_id",
                how="inner",
            )
        return out_df

    def get_persons_df(self) -> pd.DataFrame:
        raise NotImplementedError

    def _build_person_set_collection(
        self,
        psc_config: PersonSetCollectionConfig,
        families: FamiliesData,
    ) -> PersonSetCollection:
        raise NotImplementedError
