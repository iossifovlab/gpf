# pylint: disable=too-many-lines
import os
import math
import logging
from typing import Dict, Iterable, Any, List, cast
from typing import Optional, Sequence, Union, Generator
from abc import ABC, abstractmethod

from collections import defaultdict
from itertools import chain

import csv
from io import StringIO

import pandas as pd
from sqlalchemy.sql import select, text
from sqlalchemy import not_, desc, Column

from dae.pedigrees.family import Person
from dae.pedigrees.families_data import FamiliesData
from dae.pheno.db import DbManager
from dae.pheno.common import MeasureType
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.phenotype_data import pheno_conf_schema

from dae.variants.attributes import Sex, Status, Role
from dae.utils.helpers import isnan


logger = logging.getLogger(__name__)


def get_pheno_db_dir(dae_config):
    """Return the directory where phenotype data configurations are located."""
    if dae_config is not None:
        if dae_config.phenotype_data is None or \
                dae_config.phenotype_data.dir is None:
            pheno_data_dir = os.path.join(
                dae_config.conf_dir, "pheno")
        else:
            pheno_data_dir = dae_config.phenotype_data.dir
    else:
        pheno_data_dir = os.path.join(
            os.environ.get("DAE_DB_DIR", ""), "pheno")

    return pheno_data_dir


def get_pheno_browser_images_dir(dae_config=None):
    pheno_db_dir = os.environ.get(
        "DAE_PHENODB_DIR",
        get_pheno_db_dir(dae_config)
    )
    browser_images_path = os.path.join(pheno_db_dir, "images")
    return browser_images_path


class Instrument:
    """
    Instrument object represents phenotype instruments.

    Common fields are:

    * `instrument_name`

    * `measures` -- dictionary of all measures in the instrument
    """

    def __init__(self, name: str):
        self.instrument_name = name
        self.measures: Dict[str, Measure] = {}

    def __repr__(self):
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

    def __init__(self, measure_id: str, name: str):
        self.measure_id = measure_id
        self.name: str = name
        self.measure_name: str = name
        self.measure_type: MeasureType = MeasureType.other
        self.values_domain: Optional[str] = None
        self.instrument_name: Optional[str] = None
        self.description: Optional[str] = None
        self.default_filter = None
        self.min_value = None
        self.max_value = None

    def __repr__(self):
        return f"Measure({self.measure_id}, " \
            f"{self.measure_type}, {self.values_domain})"

    @property
    def domain(self) -> Sequence[Union[str, float]]:
        """Return measure values domain."""
        domain_list: Sequence[Union[str, float]] = []
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
    def _from_record(cls, row):
        """Create `Measure` object from pandas data frame row."""
        assert row["measure_type"] is not None

        mes = Measure(row["measure_id"], row["measure_name"])
        mes.instrument_name = row["instrument_name"]
        mes.measure_name = row["measure_name"]
        mes.measure_type = row["measure_type"]

        mes.description = row["description"]
        mes.default_filter = row["default_filter"]
        mes.values_domain = row.get("values_domain")
        mes.min_value = row.get("min_value")
        mes.max_value = row.get("max_value")

        return mes

    @classmethod
    def from_json(cls, json):
        """Create `Measure` object from a JSON representation."""
        assert json["measureType"] is not None

        mes = Measure(json["measureId"], json["measureName"])
        mes.instrument_name = json["instrumentName"]
        mes.measure_name = json["measureName"]
        mes.measure_type = MeasureType.from_str(json["measureType"])
        mes.description = json["description"]
        mes.default_filter = json["defaultFilter"]
        mes.values_domain = json.get("valuesDomain")
        mes.min_value = json.get("minValue")
        mes.max_value = json.get("maxValue")

        return mes

    def to_json(self):
        """Return measure description in JSON freindly format."""
        result: Dict[str, Any] = {}

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

    def __init__(self, pheno_id: str):
        self._pheno_id: str = pheno_id
        self._measures: Dict[str, Measure] = {}
        self._instruments: Dict[str, Instrument] = {}
        self.families: FamiliesData

    @property
    def pheno_id(self) -> str:
        return self._pheno_id

    @property
    def measures(self) -> Dict[str, Measure]:
        return self._measures

    @property
    def instruments(self) -> Dict[str, Instrument]:
        return self._instruments

    def get_instruments(self):
        return self.instruments.keys()

    @abstractmethod
    def get_regressions(self):
        pass

    @abstractmethod
    def get_measures_info(self):
        pass

    @abstractmethod
    def get_persons_df(
            self, roles: Optional[List[Role]] = None,
            person_ids: Optional[List[str]] = None,
            family_ids: Optional[List[str]] = None) -> pd.DataFrame:
        pass

    def get_persons(
            self,
            roles: Optional[List[Role]] = None,
            person_ids: Optional[List[str]] = None,
            family_ids: Optional[List[str]] = None) -> Dict[str, Person]:
        """
        Return individuals data from phenotype database.

        `roles` -- specifies persons of which role should be returned. If not
        specified returns all individuals from phenotype database.

        `person_ids` -- list of person IDs to filter result. Only data for
        individuals with person_id in the list `person_ids` are returned.

        `family_ids` -- list of family IDs to filter result. Only data for
        individuals that are members of any of the specified `family_ids`
        are returned.

        Returns a dictionary of (`personId`, `Person()`) where
        the `Person` object is the same object used into `VariantDB` families.
        """
        persons = {}
        df = self.get_persons_df(
            roles=roles, person_ids=person_ids, family_ids=family_ids)

        for row in df.to_dict("records"):
            person_id = row["person_id"]

            person = Person(**row)  # type: ignore
            assert row["role"] in Role, f"{row['role']} not a valid role"
            assert row["sex"] in Sex, f"{row['sex']} not a valid sex"
            assert row["status"] in Status, \
                f"{row['status']} not a valid status"

            persons[person_id] = person
        return persons

    @abstractmethod
    def search_measures(self, instrument, search_term):
        pass

    def has_measure(self, measure_id: str) -> bool:
        """Check if phenotype DB contains a measure by ID."""
        return measure_id in self._measures

    def get_measure(self, measure_id: str) -> Measure:
        """Return a measure by measure_id."""
        assert measure_id in self._measures, measure_id
        return self._measures[measure_id]

    def get_measures(
            self,
            instrument_name: Optional[str] = None,
            measure_type: Optional[str] = None) -> Dict[str, Measure]:
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
                instrument_name: self.instruments[instrument_name]
            }

        if measure_type is not None:
            measure_type = MeasureType.from_str(measure_type)

        for instrument_name, instrument in instruments.items():
            for measure in instrument.measures.values():
                if measure_type is not None and \
                        measure.measure_type != measure_type:
                    continue
                result[measure.measure_id] = measure

        return result

    def get_measure_description(self, measure_id):
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

    @abstractmethod
    def get_measure_values_df(
            self,
            measure_id: str,
            person_ids: Optional[Iterable[str]] = None,
            family_ids: Optional[Iterable[str]] = None,
            roles: Optional[Iterable[Role]] = None,
            default_filter: str = "apply") -> pd.DataFrame:
        """Return a data frame with values for the specified `measure_id`.

        :param measure_id: -- a measure ID which values should be returned.

        :param person_ids: -- list of person IDs to filter result. Only data
        for individuals with person_id in the list `person_ids` are returned.

        :param family_ids: -- list of family IDs to filter result. Only data
        for individuals that are members of any of the specified `family_ids`
        are returned.

        :param roles: -- list of roles of individuals to select measure value
        for. If not specified value for individuals in all roles are returned.

        :param default_filter: -- one of ('`skip`', '`apply`', '`invert`').
        When the measure has a `default_filter` this argument specifies whether
        the filter should be applied or skipped or inverted.

        The returned data frame contains values of the measure for
        each individual. The person_id is used as key in the dictionary.
        """

    def get_measure_values(
            self,
            measure_id: str,
            person_ids: Optional[Iterable[str]] = None,
            family_ids: Optional[Iterable[str]] = None,
            roles: Optional[Iterable[Role]] = None,
            default_filter: str = "apply") -> Dict[str, Any]:
        """Return a dictionary with values for the specified `measure_id`.

        :param measure_id: -- a measure ID which values should be returned.

        :param person_ids: -- list of person IDs to filter result. Only data
        for individuals with person_id in the list `person_ids` are returned.

        :param family_ids: -- list of family IDs to filter result. Only data
        for individuals that are members of any of the specified `family_ids`
        are returned.

        :param roles: -- list of roles of individuals to select measure value
        for. If not specified value for individuals in all roles are returned.

        :param default_filter: -- one of ('`skip`', '`apply`', '`invert`').
        When the measure has a `default_filter` this argument specifies whether
        the filter should be applied or skipped or inverted.

        The returned dictionary contains values of the measure for
        each individual. The person_id is used as key in the dictionary.
        """
        df = self.get_measure_values_df(
            measure_id,
            person_ids=person_ids,
            family_ids=family_ids,
            roles=roles,
            default_filter=default_filter)

        res = {}
        for row in df.to_dict("records"):
            res[row["person_id"]] = row[measure_id]
        return res

    @abstractmethod
    def get_values_df(
            self,
            measure_ids: Iterable[str],
            person_ids: Optional[Iterable[str]] = None,
            family_ids: Optional[Iterable[str]] = None,
            roles: Optional[Iterable[Role]] = None,
            default_filter: str = "apply") -> pd.DataFrame:
        """Return a data frame with values for all `measure_ids`.

        :param measure_ids: -- list of measure IDs which values should be
        returned.

        :param person_ids: -- list of person IDs to filter result. Only data
        for individuals with person_id in the list `person_ids` are returned.

        :param family_ids: -- list of family IDs to filter result. Only data
        for individuals that are members of any of the specified `family_ids`
        are returned.

        :param roles: -- list of roles of individuals to select measure value
        for. If not specified value for individuals in all roles are returned.

        :param default_filter: -- one of ('`skip`', '`apply`', '`invert`').
        When the measure has a `default_filter` this argument specifies whether
        the filter should be applied or skipped or inverted.
        """

    def get_values(
            self,
            measure_ids: Iterable[str],
            person_ids: Optional[Iterable[str]] = None,
            family_ids: Optional[Iterable[str]] = None,
            roles: Optional[Iterable[Role]] = None,
            default_filter: str = "apply") -> Dict[str, Dict[str, Any]]:
        """Return dictionary of dictionaries with values for all `measure_ids`.

        The returned dictionary uses `person_id` as key. The value for each key
        is a dictionary of measurement values for each ID in `measure_ids`
        keyed measure_id.

        :param measure_ids: -- list of measure IDs which values should be
        returned.

        :param person_ids: -- list of person IDs to filter result. Only data
        for individuals with person_id in the list `person_ids` are returned.

        :param family_ids: -- list of family IDs to filter result. Only data
        for individuals that are members of any of the specified `family_ids`
        are returned.

        :param roles: -- list of roles of individuals to select measure value
        for. If not specified value for individuals in all roles are returned.

        :param default_filter: -- one of ('`skip`', '`apply`', '`invert`').
        When the measure has a `default_filter` this argument specifies whether
        the filter should be applied or skipped or inverted.
        """
        df = self.get_values_df(
            measure_ids, person_ids, family_ids, roles, default_filter)
        res: Dict[str, Dict[str, Any]] = {}
        for row in df.to_dict("records"):
            person_id = str(row["person_id"])
            res[person_id] = cast(Dict[str, Any], row)

        return res

    def get_persons_values_df(
            self,
            measure_ids: Iterable[str],
            person_ids: Optional[List[str]] = None,
            family_ids: Optional[List[str]] = None,
            roles: Optional[List[Role]] = None,
            default_filter: str = "apply") -> pd.DataFrame:
        """
        Return a data frame with measure values and person data.

        Collects values for all measures in `measure_ids` and
        joins with data frame returned by `get_persons_df`.
        """
        persons_df = self.get_persons_df(
            roles=roles, person_ids=person_ids, family_ids=family_ids)

        value_df = self.get_values_df(
            measure_ids,
            person_ids=person_ids,
            family_ids=family_ids,
            roles=roles,
            default_filter=default_filter)

        df = persons_df.join(
            value_df.set_index("person_id"),
            on="person_id",
            how="right",
            rsuffix="_val")  # type: ignore
        df = df.set_index("person_id")
        df = df.reset_index()

        return df

    def _get_instrument_measures(self, instrument_name: str) -> List[str]:
        """Return measures for given instrument."""
        assert instrument_name in self.instruments
        instrument = self.instruments[instrument_name]
        measure_ids = [
            m.measure_id for m in list(instrument.measures.values())
        ]
        return measure_ids

    def get_instrument_values_df(
            self, instrument_name,
            person_ids=None,
            family_ids=None,
            role=None,
            measure_ids=None):
        """
        Return a dataframe with values for measures in given instrument.

        If not supplied a list of measure IDs, it will use all
        measures in the given instrument
        (see **get_values_df**)
        """
        if measure_ids is None:
            measure_ids = self._get_instrument_measures(instrument_name)
        res = self.get_values_df(measure_ids, person_ids, family_ids, role)
        return res

    def get_instrument_values(
            self, instrument_name,
            person_ids=None,
            family_ids=None,
            role=None,
            measure_ids=None):
        """
        Return a dictionary with values for measures in given instrument.

        If not supplied a list of measure IDs, it will use all
        measures in the given instrument
        (see :func:`get_values`)
        """
        if measure_ids is None:
            measure_ids = self._get_instrument_measures(instrument_name)
        return self.get_values(measure_ids, person_ids, family_ids, role)

    @abstractmethod
    def get_values_streaming_csv(
        self,
        measure_ids: list[str],
        person_ids: Optional[list[str]] = None,
        family_ids: Optional[list[str]] = None,
        roles: Optional[list[str]] = None,
    ) -> Generator[str, None, None]:
        """
        Collect and format the values of the given measures in CSV format.

        Yields lines.

        `measure_ids` -- list of measure ids which values should be returned.

        `person_ids` -- list of person IDs to filter result. Only data for
        individuals with person_id in the list `person_ids` are returned.

        `family_ids` -- list of family IDs to filter result. Only data for
        individuals that are members of any of the specified `family_ids`
        are returned.

        `roles` -- list of roles of individuals to select measure value for.
        If not specified value for individuals in all roles are returned.
        """
        raise NotImplementedError()


class PhenotypeStudy(PhenotypeData):
    """
    Main class for accessing phenotype database in DAE.

    To access the phenotype database create an instance of this class
    and call the method *load()*.

    Common fields of this class are:

    * `families` -- list of all families in the database

    * `persons` -- list of all individuals in the database

    * `instruments` -- dictionary of all instruments

    * `measures` -- dictionary of all measures
    """

    def __init__(
            self, pheno_id: str, dbfile: str,
            browser_dbfile: Optional[str] = None,
            config: Optional[Dict[str, str]] = None):

        super().__init__(pheno_id)

        self.db = DbManager(dbfile=dbfile, browser_dbfile=browser_dbfile)
        self.config = config
        self.db.build()
        self.families = self._load_families()
        self._instruments = self._load_instruments()

    def _get_measures_df(self, instrument=None, measure_type=None):
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
        assert measure_type is None or measure_type in set(
            ["continuous", "ordinal", "categorical", "unknown"]
        )

        measure = self.db.measure
        columns = [
            measure.c.measure_id,
            measure.c.instrument_name,
            measure.c.measure_name,
            measure.c.description,
            measure.c.measure_type,
            measure.c.individuals,
            measure.c.default_filter,
            measure.c.values_domain,
            measure.c.min_value,
            measure.c.max_value,
        ]
        query = select(*columns)
        query = query.where(not_(measure.c.measure_type.is_(None)))
        if instrument is not None:
            query = query.where(measure.c.instrument_name == instrument)
        if measure_type is not None:
            query = query.where(measure.c.measure_type == measure_type)

        df = pd.read_sql(query, self.db.pheno_engine)

        df_columns = [
            "measure_id",
            "measure_name",
            "instrument_name",
            "description",
            "individuals",
            "measure_type",
            "default_filter",
            "values_domain",
            "min_value",
            "max_value",
        ]
        res_df = df[df_columns]
        return res_df

    def _load_instruments(self):
        instruments = {}

        df = self._get_measures_df()
        instrument_names = list(df.instrument_name.unique())
        instrument_names = sorted(instrument_names)

        for instrument_name in instrument_names:
            instrument = Instrument(instrument_name)
            measures = {}
            measures_df = df[df.instrument_name == instrument_name]

            for row in measures_df.to_dict("records"):
                # pylint: disable=protected-access
                measure = Measure._from_record(row)
                measures[measure.measure_name] = measure
                self._measures[measure.measure_id] = measure
            instrument.measures = measures
            instruments[instrument.instrument_name] = instrument

        return instruments

    def _load_families(self):
        families = defaultdict(list)
        persons = self.get_persons()
        for person in list(persons.values()):
            families[person.family_id].append(person)
        return FamiliesData.from_family_persons(families)

    def get_persons_df(self, roles=None, person_ids=None, family_ids=None):
        """Return a individuals data from phenotype database as a data frame.

        :param roles: -- specifies persons of which role should be returned. If
        not specified returns all individuals from phenotype database.

        :param person_ids: -- list of person IDs to filter result. Only data
        for individuals with person_id in the list `person_ids` are returned.

        :param family_ids: -- list of family IDs to filter result. Only data
        for individuals that are members of any of the specified `family_ids`
        are returned.

        Each row of the returned data frame represnts a person from phenotype
        database.

        Columns returned are: `person_id`, `family_id`, `role`, `sex`.
        """
        columns = [
            self.db.family.c.family_id,
            self.db.person.c.person_id,
            self.db.person.c.role,
            self.db.person.c.status,
            self.db.person.c.sex,
        ]
        query = select(*columns)
        query = query.select_from(self.db.family.join(self.db.person))
        if roles is not None:
            query = query.where(self.db.person.c.role.in_(roles))
        if person_ids is not None:
            query = query.where(self.db.person.c.person_id.in_(person_ids))
        if family_ids is not None:
            query = query.where(self.db.family.c.family_id.in_(family_ids))
        df = pd.read_sql(query, self.db.pheno_engine)
        # df.rename(columns={'sex': 'sex'}, inplace=True)
        return df[["person_id", "family_id", "role", "sex", "status"]]

    def _build_default_filter_clause(self, measure, default_filter):
        if default_filter == "skip" or measure.default_filter is None:
            return None
        if default_filter == "apply":
            return f"value {measure.default_filter}"
        if default_filter == "invert":
            return f"NOT (value {measure.default_filter})"

        raise ValueError(
            f"bad default_filter value: {default_filter}"
        )

    def _raw_get_measure_values_df(
        self,
        measure,
        person_ids=None,
        family_ids=None,
        roles=None,
        default_filter="skip",
    ):

        measure_type = measure.measure_type
        if measure_type is None:
            raise ValueError(
                f"bad measure: {measure.measure_id}; unknown value type"
            )
        value_table = self.db.get_value_table(measure_type)
        columns = [
            self.db.family.c.family_id,
            self.db.person.c.person_id,
            self.db.person.c.sex,
            self.db.person.c.status,
            value_table.c.value,
        ]

        query = select(*columns)
        query = query.select_from(
            value_table.join(self.db.measure)
            .join(self.db.person)
            .join(self.db.family)
        )
        query = query.where(self.db.measure.c.measure_id == measure.measure_id)

        if roles is not None:
            query = query.where(self.db.person.c.role.in_(roles))
        if person_ids is not None:
            query = query.where(self.db.person.c.person_id.in_(person_ids))
        if family_ids is not None:
            query = query.where(self.db.family.c.family_id.in_(family_ids))

        if measure.default_filter is not None:
            filter_clause = self._build_default_filter_clause(
                measure, default_filter
            )
            if filter_clause is not None:
                query = query.where(text(filter_clause))

        df = pd.read_sql(query, self.db.pheno_engine)
        df.rename(columns={"value": measure.measure_id}, inplace=True)
        return df

    def get_measure_values_df(
            self,
            measure_id,
            person_ids=None,
            family_ids=None,
            roles=None,
            default_filter="apply"):
        """Return a data frame with values for the specified `measure_id`.

        :param measure_id: -- a measure ID which values should be returned.

        :param person_ids: -- list of person IDs to filter result. Only data
        forindividuals with person_id in the list `person_ids` are returned.

        :param family_ids: -- list of family IDs to filter result. Only data
        for individuals that are members of any of the specified `family_ids`
        are returned.

        :param roles: -- list of roles of individuals to select measure value
        for. If not specified value for individuals in all roles are retuned.

        :param default_filter: -- one of ('`skip`', '`apply`', '`invert`').
        When the measure has a `default_filter` this argument specifies whether
        the filter should be applied or skipped or inverted.

        The returned data frame contains two columns: `person_id` for
        individuals IDs and column named as `measure_id` values of the measure.
        """
        assert measure_id in self.measures, measure_id
        measure = self.measures[measure_id]

        df = self._raw_get_measure_values_df(
            measure,
            person_ids=person_ids,
            family_ids=family_ids,
            roles=roles,
            default_filter=default_filter,
        )
        return df[["person_id", measure_id]]

    def get_values_df(
            self,
            measure_ids,
            person_ids=None,
            family_ids=None,
            roles=None,
            default_filter="apply"):
        """Return a data frame with values for given list of measures.

        Values are loaded using consecutive calls to
        `get_measure_values_df()` method for each measure in `measure_ids`.
        All data frames are joined in the end and returned.

        :param measure_ids: -- list of measure ids which values should be
        returned.

        :param person_ids: -- list of person IDs to filter result. Only data
        for individuals with person_id in the list `person_ids` are returned.

        :param family_ids: -- list of family IDs to filter result. Only data
        for individuals that are members of any of the specified `family_ids`
        are returned.

        :param roles: -- list of roles of individuals to select measure value
        for. If not specified value for individuals in all roles are returned.
        """
        assert isinstance(measure_ids, list)
        assert len(measure_ids) >= 1
        assert all([self.has_measure(m) for m in measure_ids])

        dfs = [
            self.get_measure_values_df(
                m, person_ids, family_ids, roles, default_filter
            )
            for m in measure_ids
        ]

        res_df = dfs[0]
        for i, df in enumerate(dfs[1:]):
            res_df = res_df.join(
                df.set_index("person_id"),
                on="person_id",
                how="outer",
                rsuffix=f"_val_{i}",
            )

        return res_df

    def _build_measures_subquery(
        self,
        measure_id_map: dict[str, str],
        measure_ids: list[str],
        person_ids: Optional[list[str]] = None,
        family_ids: Optional[list[str]] = None,
        roles: Optional[list[str]] = None,
    ):
        select_columns = [
            self.db.person.c.person_id
        ]
        for m_id in measure_ids:
            measure = self.measures[m_id]
            measure_type = measure.measure_type
            if measure_type is None:
                raise ValueError(
                    f"bad measure: {measure.measure_id}; unknown value type"
                )
            select_columns.append(cast(Column[Any], text(
                f"\"{m_id}_value\".value AS '{m_id}'"
            )))
        query = select(*select_columns).select_from(
            self.db.person.join(self.db.family)
        )

        for m_id in measure_ids:
            db_id = measure_id_map[m_id]
            measure = self.measures[m_id]
            measure_type = self.measures[m_id].measure_type
            measure_table = self.db.get_value_table(measure_type)
            table_alias = f"{m_id}_value"
            query = query.join(
                text(f'{measure_table.name} as "{table_alias}"'),
                text(
                    f'"{table_alias}".person_id = person.id AND '
                    f'"{table_alias}".measure_id = {db_id}'
                ),
                isouter=True
            )

        if roles is not None:
            query = query.where(self.db.person.c.role.in_(roles))
        if person_ids is not None:
            query = query.where(self.db.person.c.person_id.in_(person_ids))
        if family_ids is not None:
            query = query.where(self.db.family.c.family_id.in_(family_ids))

        query = query.order_by(desc(self.db.person.c.person_id))
        return query

    def _split_measures_into_groups(
        self, measure_ids: list[str], group_size: int = 60
    ) -> list[list[str]]:
        groups_count = int(len(measure_ids) / group_size) + 1
        if (groups_count) == 1:
            return [measure_ids]
        measure_groups = []
        for i in range(groups_count):
            begin = i * group_size
            end = (i + 1) * group_size
            measure_groups.append(measure_ids[begin:end])
        return measure_groups


    def get_values_streaming_csv(
        self,
        measure_ids: list[str],
        person_ids: Optional[list[str]] = None,
        family_ids: Optional[list[str]] = None,
        roles: Optional[list[str]] = None,
    ) -> Generator[str, None, None]:
        assert isinstance(measure_ids, list)
        assert len(measure_ids) >= 1
        assert all(self.has_measure(m) for m in measure_ids)

        measure_id_map = {m_id: None for m_id in measure_ids}
        with self.db.pheno_engine.connect() as connection:
            query = select(
                self.db.measure.c.id, self.db.measure.c.measure_id
            ).where(self.db.measure.c.measure_id.in_(measure_ids))
            results = connection.execute(query)
            for row in results:
                measure_id_map[row.measure_id] = row.id

        header = ["person_id"] + measure_ids

        buffer = StringIO()
        writer = csv.writer(buffer, delimiter=",")
        writer.writerow(header)
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)

        measure_groups = self._split_measures_into_groups(measure_ids)

        queries = []
        for group in measure_groups:
            queries.append(self._build_measures_subquery(
                cast(dict[str, str], measure_id_map),
                group,
                person_ids,
                family_ids,
                roles
            ))


        with self.db.pheno_engine.connect() as connection:
            query_results = []
            for query in queries:
                query_results.append(connection.execute(query))
            for row in query_results[0]:
                output = [row.person_id]
                skip = True
                row = row._mapping  # pylint: disable=protected-access
                for measure_id in measure_groups[0]:
                    value = row[measure_id]
                    if value is None or value == "":
                        value = "-"
                    else:
                        skip = False
                    output.append(value)
                if len(query_results) > 1:
                    for i in range(1, len(measure_groups)):
                        # pylint: disable=protected-access
                        try:
                            row = next(query_results[i])._mapping
                        except StopIteration:
                            logger.error(
                                "Subquery %s has different length",
                                i
                            )
                            continue
                        for measure_id in measure_groups[i]:
                            value = row[measure_id]
                            if value is None or value == "":
                                value = "-"
                            else:
                                skip = False
                            output.append(value)
                if skip:
                    continue
                writer.writerow(output)
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)

        buffer.close()

    def get_regressions(self) -> dict[str, Any]:
        return cast(dict[str, Any], self.db.regression_display_names_with_ids)

    def _get_pheno_images_base_url(self) -> Optional[str]:
        return None if self.config is None \
            else self.config.get("browser_images_url")

    def get_measures_info(self) -> dict[str, Any]:
        return {
            "base_image_url": self._get_pheno_images_base_url(),
            "has_descriptions": self.db.has_descriptions,
            "regression_names": self.db.regression_display_names,
        }

    def search_measures(
        self, instrument: Optional[str], search_term: Optional[str]
    ) -> Generator[dict[str, Any], None, None]:
        measures = self.db.search_measures(instrument, search_term)

        for measure in measures:
            if measure["values_domain"] is None:
                measure["values_domain"] = ""
            measure["measure_type"] = measure["measure_type"].name

            measure["regressions"] = []
            regressions = self.db.get_regression_values(
                measure["measure_id"]) or []

            for reg in regressions:
                reg = reg._mapping  # pylint: disable=protected-access
                if isnan(reg["pvalue_regression_male"]):
                    reg["pvalue_regression_male"] = "NaN"
                if isnan(reg["pvalue_regression_female"]):
                    reg["pvalue_regression_female"] = "NaN"
                measure["regressions"].append(dict(reg))

            yield {
                "measure": measure,
            }


class PhenotypeGroup(PhenotypeData):
    """Represents a group of phenotype data studies or groups."""

    def __init__(
            self, pheno_id: str, phenotype_data: List[PhenotypeData],
            config=None):
        super().__init__(pheno_id)
        self.phenotype_data = phenotype_data
        self.families = self._build_families()
        instruments, measures = self._merge_instruments(
            [ph.instruments for ph in self.phenotype_data])
        self._instruments.update(instruments)

        self._measures.update(measures)
        self.config = config

    def _build_families(self):
        phenos = self.phenotype_data
        logger.info(
            "building combined families from phenotype data: %s",
            [st.pheno_id for st in phenos])

        if len(phenos) == 1:
            return FamiliesData.copy(phenos[0].families)

        logger.info(
            "combining families from phenotype data %s and %s",
            phenos[0].pheno_id, phenos[1].pheno_id)
        result = FamiliesData.combine(
            phenos[0].families,
            phenos[1].families)

        if len(phenos) > 2:
            for sind in range(2, len(phenos)):
                logger.debug(
                    "processing pheno (%s): %s", sind, phenos[sind].pheno_id)
                logger.info(
                    "combining families from pheno (%s) %s with families "
                    "from pheno %s",
                    sind, [st.pheno_id for st in phenos[:sind]],
                    phenos[sind].pheno_id)
                result = FamiliesData.combine(
                    result,
                    phenos[sind].families,
                    forced=True)
        return result

    @staticmethod
    def _merge_instruments(
            phenos_instruments: Iterable[Dict[str, Instrument]]):
        group_instruments: Dict[str, Instrument] = {}
        group_measures: Dict[str, Measure] = {}

        for pheno_instruments in phenos_instruments:
            for instrument_name, instrument in pheno_instruments.items():
                if instrument_name not in group_instruments:
                    group_instrument = Instrument(
                        instrument_name
                    )
                else:
                    group_instrument = group_instruments[instrument_name]

                for name, measure in instrument.measures.items():
                    full_name = f"{instrument_name}.{name}"
                    if full_name in group_measures:
                        logger.warning(
                            "%s measure duplication! ignoring", full_name)
                        del group_instrument.measures[full_name]
                        del group_measures[full_name]
                        continue
                    group_instrument.measures[full_name] = measure
                    group_measures[full_name] = measure
                group_instruments[instrument_name] = group_instrument

        # group_instruments = {}
        # group_measures = {}
        # for pheno_instruments in phenos_instruments:
        #     for instrument_name, instrument in pheno_instruments.items():
        #         if instrument_name not in group_instruments:
        #             group_instruments[instrument_name] = instrument
        #             group_measures.update({
        #                 f"{instrument_name}.{name}": measure
        #                 for name, measure in instrument.measures.items()
        #             })
        #         else:
        #             # try to merge instrument
        #             logger.info(
        #                 f"trying to merge instrument {instrument_name}")

        #             group_instrument = group_instruments[instrument_name]
        #             assert group_instrument.instrument_name == \
        #                 instrument_name

        #             measure_ids = set(instrument.keys())
        #             group_measure_ids = set(group_instrument.measures.keys())

        #             if measure_ids & group_measure_ids:
        #                 msg = f"can't merge instruments because of " \
        #                     f"measures {measure_ids & group_measure_ids}"
        #                 logger.error(msg)
        #                 raise ValueError(msg)
        #             group_instrument.measures.update(instrument.measures)
        #             group_measures.update({
        #                 f"{instrument_name}.{name}": measure
        #                 for name, measure in instrument.measures.items()
        #             })

        return group_instruments, group_measures

    def get_persons_df(
            self, roles: Optional[List[Role]] = None,
            person_ids: Optional[List[str]] = None,
            family_ids: Optional[List[str]] = None) -> pd.DataFrame:

        ped_df: pd.DataFrame = self.families.ped_df[[
            "person_id", "family_id", "role", "sex", "status"]]

        if roles is not None:
            ped_df = ped_df[ped_df.role.isin(roles)]
        if person_ids is not None:
            ped_df = ped_df[ped_df.person_id.isin(person_ids)]
        if family_ids is not None:
            ped_df = ped_df[ped_df.family_id.isin(family_ids)]
        return ped_df

    def get_measure_values_df(
            self,
            measure_id: str,
            person_ids: Optional[Iterable[str]] = None,
            family_ids: Optional[Iterable[str]] = None,
            roles: Optional[Iterable[Role]] = None,
            default_filter: str = "apply") -> pd.DataFrame:

        assert self.has_measure(measure_id), measure_id
        for pheno in self.phenotype_data:
            if pheno.has_measure(measure_id):
                return pheno.get_measure_values_df(
                    measure_id,
                    person_ids=person_ids,
                    family_ids=family_ids,
                    roles=roles,
                    default_filter=default_filter
                )

        # We should never get here
        msg = f"measure {measure_id} not found in phenotype group " \
            f"{self.pheno_id}"
        logger.error(msg)
        raise ValueError(msg)

    def get_values_df(
            self,
            measure_ids: Iterable[str],
            person_ids: Optional[Iterable[str]] = None,
            family_ids: Optional[Iterable[str]] = None,
            roles: Optional[Iterable[Role]] = None,
            default_filter: str = "apply") -> pd.DataFrame:

        assert all([self.has_measure(mid) for mid in measure_ids]), measure_ids

        dfs = []
        for pheno in self.phenotype_data:
            pheno_measure_ids = []
            for mid in measure_ids:
                if pheno.has_measure(mid):
                    pheno_measure_ids.append(mid)
            if pheno_measure_ids:
                df = pheno.get_values_df(
                    pheno_measure_ids,
                    person_ids=person_ids,
                    family_ids=family_ids,
                    roles=roles,
                    default_filter=default_filter)
                dfs.append(df)
        assert len(dfs) > 0
        if len(dfs) == 1:
            return dfs[0]

        res_df = dfs[0]
        for i, df in enumerate(dfs[1:]):
            res_df = res_df.join(
                df.set_index("person_id"),
                on="person_id",
                how="outer",
                rsuffix=f"_val_{i}")

        return res_df

    def get_regressions(self):
        res = []
        for pheno in self.phenotype_data:
            res += pheno.get_regressions()
        return res

    def get_measures_info(self):
        result = {
            "base_image_url": "",
            "has_descriptions": False,
            "regression_names": {}
        }
        for pheno in self.phenotype_data:
            measures_info = pheno.get_measures_info()
            result["has_descriptions"] = \
                result["has_descriptions"] or measures_info["has_descriptions"]
            cast(Dict, result["regression_names"]).update(
                measures_info["regression_names"]
            )
        return result

    def search_measures(self, instrument, search_term):
        generators = [
            pheno.search_measures(instrument, search_term)
            for pheno in self.phenotype_data
        ]
        measures = chain(*generators)
        yield from measures

    def get_values_streaming_csv(
        self,
        measure_ids: list[str],
        person_ids: Optional[list[str]] = None,
        family_ids: Optional[list[str]] = None,
        roles: Optional[list[str]] = None,
    ) -> Generator[str, None, None]:
        raise NotImplementedError()


class PhenoDb:
    """Represents a phenotype databases stored in an sqlite database."""

    def __init__(self, dae_config):
        super().__init__()
        assert dae_config
        pheno_data_dir = get_pheno_db_dir(dae_config)

        configs = GPFConfigParser.load_directory_configs(
            pheno_data_dir, pheno_conf_schema
        )

        self.config = {
            config.phenotype_data.name: config.phenotype_data
            for config in configs
            if config.phenotype_data and config.phenotype_data.enabled
        }

        self.pheno_cache: Dict[str, PhenotypeData] = {}

    def get_dbfile(self, pheno_id):
        return self.config[pheno_id].dbfile

    def get_browser_dbfile(self, pheno_id):
        return self.config[pheno_id].browser_dbfile

    def get_dbconfig(self, pheno_id):
        return self.config[pheno_id]

    def has_phenotype_data(self, pheno_id):
        return pheno_id in self.config

    def get_phenotype_data_ids(self):
        return list(self.config.keys())

    def get_phenotype_data(self, pheno_id) -> PhenotypeData:
        """Construct and return a phenotype data with the specified ID."""
        if not self.has_phenotype_data(pheno_id):
            raise ValueError(f"phenotype data <{pheno_id}> not found")
        if pheno_id in self.pheno_cache:
            return self.pheno_cache[pheno_id]

        phenotype_data: PhenotypeData
        config = self.get_dbconfig(pheno_id)
        if config.phenotype_data_list is not None:
            logger.info("loading pheno db group <%s>", pheno_id)
            phenotype_studies = [
                self.get_phenotype_data(ps_id)
                for ps_id in config.phenotype_data_list
            ]
            phenotype_data = PhenotypeGroup(
                pheno_id, phenotype_studies, config)
        else:
            logger.info("loading pheno db <%s>", pheno_id)
            phenotype_data = PhenotypeStudy(
                pheno_id,
                dbfile=self.get_dbfile(pheno_id),
                browser_dbfile=self.get_browser_dbfile(pheno_id),
                config=config
            )
        self.pheno_cache[pheno_id] = phenotype_data
        return phenotype_data

    def get_all_phenotype_data(self):
        return [
            self.get_phenotype_data(pheno_id)
            for pheno_id in self.get_phenotype_data_ids()
        ]

    def get_phenotype_data_config(self, pheno_id):
        return self.config.get(pheno_id)
