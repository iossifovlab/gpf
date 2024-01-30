# pylint: disable=too-many-lines
from __future__ import annotations
import os
import math
import logging
from typing import Iterable, Any, cast
from typing import Optional, Sequence, Union, Generator
from abc import ABC, abstractmethod

from collections import defaultdict
from itertools import chain
from box import Box

import pandas as pd
from sqlalchemy.sql import select, text, union
from sqlalchemy import not_, Select

from dae.pedigrees.family import Person
from dae.pedigrees.families_data import FamiliesData
from dae.pheno.db import PhenoDb
from dae.pheno.common import MeasureType
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.phenotype_data import pheno_conf_schema

from dae.variants.attributes import Sex, Status, Role
from dae.utils.helpers import isnan


logger = logging.getLogger(__name__)


def get_pheno_db_dir(dae_config: Optional[Box]) -> str:
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


def get_pheno_browser_images_dir(dae_config: Optional[Box] = None) -> str:
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
        self.values_domain: Optional[str] = None
        self.instrument_name: Optional[str] = None
        self.description: Optional[str] = None
        self.default_filter = None
        self.min_value = None
        self.max_value = None

    def __repr__(self) -> str:
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
    def _from_record(cls, row: dict[str, Any]) -> Measure:
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
    def from_json(cls, json: dict[str, Any]) -> Measure:
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

    def __init__(self, pheno_id: str) -> None:
        self._pheno_id: str = pheno_id
        self._measures: dict[str, Measure] = {}
        self._instruments: dict[str, Instrument] = {}
        self.families: FamiliesData

    @property
    def pheno_id(self) -> str:
        return self._pheno_id

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
    def get_persons_df(
            self, roles: Optional[Iterable[Role]] = None,
            person_ids: Optional[Iterable[str]] = None,
            family_ids: Optional[Iterable[str]] = None) -> pd.DataFrame:
        pass

    def get_persons(
            self,
            roles: Optional[Iterable[Role]] = None,
            person_ids: Optional[Iterable[str]] = None,
            family_ids: Optional[Iterable[str]] = None) -> dict[str, Person]:
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
    def search_measures(
        self, instrument: Optional[str], search_term: Optional[str]
    ) -> Generator[dict[str, Any], None, None]:
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
        measure_type: Optional[str] = None
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
                instrument_name: self.instruments[instrument_name]
            }

        type_query = None
        if measure_type is not None:
            type_query = MeasureType.from_str(measure_type)

        for _, instrument in instruments.items():
            for measure in instrument.measures.values():
                if type_query is not None and \
                        measure.measure_type != type_query:
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
        measure_ids = [
            m.measure_id for m in list(instrument.measures.values())
        ]
        return measure_ids

    @abstractmethod
    def get_people_measure_values(
        self,
        measure_ids: list[str],
        person_ids: Optional[list[str]] = None,
        family_ids: Optional[list[str]] = None,
        roles: Optional[list[str]] = None,
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
        raise NotImplementedError()

    def get_people_measure_values_df(
        self,
        measure_ids: list[str],
        person_ids: Optional[list[str]] = None,
        family_ids: Optional[list[str]] = None,
        roles: Optional[list[str]] = None,
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
            config: Optional[dict[str, str]] = None) -> None:

        super().__init__(pheno_id)

        self.db = PhenoDb(dbfile=dbfile, browser_dbfile=browser_dbfile)
        self.config = config
        self.db.build()
        self.families = self._load_families()
        self._instruments = self._load_instruments()

    def _get_measures_df(
        self,
        instrument: Optional[str] = None,
        measure_type: Optional[str] = None
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

    def _load_instruments(self) -> dict[str, Instrument]:
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

    def _load_families(self) -> FamiliesData:
        families = defaultdict(list)
        persons = self.get_persons()
        for person in list(persons.values()):
            families[person.family_id].append(person)
        return FamiliesData.from_family_persons(families)

    def get_persons_df(
        self, roles: Optional[Iterable[Union[str, Role]]] = None,
        person_ids: Optional[Iterable[str]] = None,
        family_ids: Optional[Iterable[str]] = None
    ) -> pd.DataFrame:
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

    def _build_default_filter_clause(
        self, measure: Measure, default_filter: str
    ) -> Optional[str]:
        if default_filter == "skip" or measure.default_filter is None:
            return None
        if default_filter == "apply":
            return f"value {measure.default_filter}"
        if default_filter == "invert":
            return f"NOT (value {measure.default_filter})"

        raise ValueError(
            f"bad default_filter value: {default_filter}"
        )

    def _get_measure_values_query(
        self,
        measure_ids: list[str],
        person_ids: Optional[list[str]] = None,
        family_ids: Optional[list[str]] = None,
        roles: Optional[list[str]] = None,
    ) -> Select:
        assert isinstance(measure_ids, list)
        assert len(measure_ids) >= 1
        assert all(self.has_measure(m) for m in measure_ids), self.measures
        assert len(self.db.instrument_values_tables) > 0

        measure_column_names = self.db.get_measure_column_names_reverse(
            measure_ids
        )

        instrument_tables = {}
        instrument_table_columns = {}

        for instrument_name, table in self.db.instrument_values_tables.items():
            skip_table = True
            for m_id in measure_ids:
                if m_id.startswith(instrument_name):
                    skip_table = False

            if skip_table:
                continue

            instrument_tables[instrument_name] = table
            table_cols = [
                c.label(measure_column_names[c.name])
                for c in table.c if c.name in measure_column_names
            ]

            instrument_table_columns[instrument_name] = table_cols

        subquery_selects = []
        for table in instrument_tables.values():
            subquery_selects.append(
                select(
                    table.c.person_id, table.c.family_id, table.c.role,
                    table.c.status, table.c.sex
                ).select_from(table)
            )

        subquery = union(*subquery_selects).subquery("instruments_people")

        select_cols = []
        for instrument_name, columns in instrument_table_columns.items():
            select_cols.extend(columns)

        query = select(
            subquery.c.person_id,
            subquery.c.family_id,
            subquery.c.role,
            subquery.c.status,
            subquery.c.sex,
            *select_cols
        )
        query = query.select_from(subquery)

        for instrument_name in instrument_table_columns:
            table = instrument_tables[instrument_name]
            query = query.join(
                table,
                subquery.c.person_id == table.c.person_id,
                isouter=True,
                full=True
            )

        if person_ids is not None:
            query = query.where(
                subquery.c.person_id.in_(person_ids)
            )
        if family_ids is not None:
            query = query.where(
                subquery.c.family_id.in_(family_ids)
            )
        if roles is not None:
            query = query.where(
                subquery.c.role.in_(roles)
            )

        return query

    def get_people_measure_values(
        self,
        measure_ids: list[str],
        person_ids: Optional[list[str]] = None,
        family_ids: Optional[list[str]] = None,
        roles: Optional[list[str]] = None,
    ) -> Generator[dict[str, Any], None, None]:
        assert isinstance(measure_ids, list)
        assert len(measure_ids) >= 1
        assert all(self.has_measure(m) for m in measure_ids)
        assert len(self.db.instrument_values_tables) > 0

        query = self._get_measure_values_query(
            measure_ids,
            person_ids=person_ids,
            family_ids=family_ids,
            roles=roles
        )

        with self.db.pheno_engine.connect() as connection:
            result = connection.execute(query)

            for row in result:
                output = {**row._mapping}  # pylint: disable=protected-access
                output["status"] = str(output["status"])
                output["sex"] = str(output["sex"])
                yield output

    def get_people_measure_values_df(
        self,
        measure_ids: list[str],
        person_ids: Optional[list[str]] = None,
        family_ids: Optional[list[str]] = None,
        roles: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        assert isinstance(measure_ids, list)
        assert len(measure_ids) >= 1
        assert all(self.has_measure(m) for m in measure_ids)
        assert len(self.db.instrument_values_tables) > 0

        query = self._get_measure_values_query(
            measure_ids,
            person_ids=person_ids,
            family_ids=family_ids,
            roles=roles
        )

        with self.db.pheno_engine.connect() as connection:
            return pd.read_sql(query, connection)

    def get_regressions(self) -> dict[str, Any]:
        return self.db.regression_display_names_with_ids

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
            measure["measure_type"] = \
                cast(MeasureType, measure["measure_type"]).name

            measure["regressions"] = []
            regressions = self.db.get_regression_values(
                measure["measure_id"]) or []

            for reg in regressions:
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
        self, pheno_id: str, phenotype_data: list[PhenotypeData],
        config: Optional[dict] = None
    ) -> None:
        super().__init__(pheno_id)
        self.phenotype_data = phenotype_data
        self.families = self._build_families()
        instruments, measures = self._merge_instruments(
            [ph.instruments for ph in self.phenotype_data])
        self._instruments.update(instruments)

        self._measures.update(measures)
        self.config = config

    def _build_families(self) -> FamiliesData:
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
        phenos_instruments: Iterable[dict[str, Instrument]]
    ) -> tuple[dict[str, Instrument], dict[str, Measure]]:
        group_instruments: dict[str, Instrument] = {}
        group_measures: dict[str, Measure] = {}

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

        return group_instruments, group_measures

    def get_persons_df(
        self, roles: Optional[Iterable[Role]] = None,
        person_ids: Optional[Iterable[str]] = None,
        family_ids: Optional[Iterable[str]] = None
    ) -> pd.DataFrame:

        ped_df: pd.DataFrame = self.families.ped_df[[
            "person_id", "family_id", "role", "sex", "status"]]

        if roles is not None:
            ped_df = ped_df[ped_df.role.isin(roles)]
        if person_ids is not None:
            ped_df = ped_df[ped_df.person_id.isin(person_ids)]
        if family_ids is not None:
            ped_df = ped_df[ped_df.family_id.isin(family_ids)]
        return ped_df

    def get_regressions(self) -> dict[str, Any]:
        res = {}
        for pheno in self.phenotype_data:
            res.update(pheno.get_regressions())
        return res

    def get_measures_info(self) -> dict[str, Any]:
        result = {
            "base_image_url": "",
            "has_descriptions": False,
            "regression_names": {}
        }
        for pheno in self.phenotype_data:
            measures_info = pheno.get_measures_info()
            result["has_descriptions"] = \
                result["has_descriptions"] or measures_info["has_descriptions"]
            cast(dict, result["regression_names"]).update(
                measures_info["regression_names"]
            )
        return result

    def search_measures(
        self, instrument: Optional[str], search_term: Optional[str]
    ) -> Generator[dict[str, Any], None, None]:
        generators = [
            pheno.search_measures(instrument, search_term)
            for pheno in self.phenotype_data
        ]
        measures = chain(*generators)
        yield from measures

    def get_people_measure_values(
        self,
        measure_ids: list[str],
        person_ids: Optional[list[str]] = None,
        family_ids: Optional[list[str]] = None,
        roles: Optional[list[str]] = None,
    ) -> Generator[dict[str, Any], None, None]:
        raise NotImplementedError()
