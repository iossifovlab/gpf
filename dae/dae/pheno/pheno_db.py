import math
import logging
from typing import Dict, Iterable, Any, List, cast
from abc import ABC, abstractmethod

import pandas as pd
from sqlalchemy.sql import select, text
from sqlalchemy import not_, desc

from collections import defaultdict

import csv
from io import StringIO

from dae.pedigrees.family import Person, FamiliesData
from dae.pheno.db import DbManager
from dae.pheno.common import MeasureType
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.phenotype_data import pheno_conf_schema
from dae.utils.dae_utils import get_pheno_db_dir, get_pheno_base_url
from itertools import chain

from dae.variants.attributes import Sex, Status, Role
from dae.utils.helpers import isnan

from typing import Optional, Sequence, Union


logger = logging.getLogger(__name__)


class Instrument(object):
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
        return "Instrument({}, {})".format(
            self.instrument_name, len(self.measures)
        )


class Measure(object):
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

    def __repr__(self):
        return "Measure({}, {}, {})".format(
            self.measure_id, self.measure_type, self.values_domain
        )

    @property
    def domain(self) -> Sequence[Union[str, float]]:
        # FIXME !
        # This must be re-done in a better way, perhaps by
        # changing how the values domain string is stored in the database...
        domain_list: Sequence[Union[str, float]] = list()
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
                return list(map(lambda x: float(x), domain_list))
        return domain_list

    @classmethod
    def _from_dict(cls, row):
        """
        Creates `Measure` object from pandas data frame row.
        """
        assert row["measure_type"] is not None

        m = Measure(row["measure_id"], row["measure_name"])
        m.instrument_name = row["instrument_name"]
        m.measure_name = row["measure_name"]
        m.measure_type = row["measure_type"]

        m.description = row["description"]
        m.default_filter = row["default_filter"]
        m.values_domain = row.get("values_domain")
        m.min_value = row.get("min_value")
        m.max_value = row.get("max_value")

        return m

    @classmethod
    def from_json(cls, json):
        """
        Creates `Measure` object from a JSON representation.
        """
        assert json["measureType"] is not None

        m = Measure(json["measureId"], json["measureName"])
        m.instrument_name = json["instrumentName"]
        m.measure_name = json["measureName"]
        m.measure_type = MeasureType.from_str(json["measureType"])

        m.description = json["description"]
        m.default_filter = json["defaultFilter"]
        m.values_domain = json.get("valuesDomain")
        m.min_value = json.get("minValue")
        m.max_value = json.get("maxValue")

        return m

    def to_json(self):
        result = dict()

        result["measureName"] = self.measure_name
        result["measureId"] = self.measure_id
        result["instrumentName"] = self.instrument_name
        result["measureType"] = self.measure_type.name
        result["description"] = self.description
        result["defaultFilter"] = self.default_filter
        result["valuesDomain"] = self.values_domain
        result["minValue"] = \
            None if math.isnan(self.min_value) else self.min_value
        result["maxValue"] = \
            None if math.isnan(self.max_value) else self.max_value

        return result


class PhenotypeData(ABC):

    def __init__(self, pheno_id: str):
        self._pheno_id: str = pheno_id
        self._measures: Dict[str, Measure] = {}
        self._instruments: Dict[str, Instrument] = {}

    @property
    def pheno_id(self) -> str:
        return self._pheno_id

    @property
    def id(self) -> str:
        return self.pheno_id

    @property
    def measures(self) -> Dict[str, Measure]:
        return self._measures

    @property
    def instruments(self) -> Dict[str, Instrument]:
        return self._instruments

    def get_instruments(self):
        return self.instruments.keys()

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

        """Returns individuals data from phenotype database.

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

            p = Person(**row)
            # p.person_id = person_id
            # p.family_id = family_id
            assert row["role"] in Role, "{} not a valid role".format(
                row["role"]
            )
            assert row["sex"] in Sex, "{} not a valid sex".format(row["sex"])
            assert row["status"] in Status, "{} not a valid status".format(
                row["status"]
            )

            persons[person_id] = p
        return persons

    def has_measure(self, measure_id: str) -> bool:
        """
        Checks is `measure_id` is value ID for measure in our phenotype DB.
        """
        return measure_id in self._measures

    def get_measure(self, measure_id: str) -> Measure:
        """
        Returns a measure by measure_id.
        """
        assert measure_id in self._measures, measure_id
        return self._measures[measure_id]

    def get_measures(
            self,
            instrument_name: str = None,
            measure_type: str = None) -> Dict[str, Measure]:
        """
        Returns a dictionary of measures objects.

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
        measure = self.measures[measure_id]

        out = {
            "instrument_name": measure.instrument_name,
            "measure_name": measure.measure_name,
            "measure_type": measure.measure_type.name,
            "values_domain": measure.domain,
        }
        if not math.isnan(measure.min_value):
            out["min_value"] = measure.min_value
        if not math.isnan(measure.max_value):
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
        pass

    def get_measure_values(
            self,
            measure_id: str,
            person_ids: Optional[Iterable[str]] = None,
            family_ids: Optional[Iterable[str]] = None,
            roles: Optional[Iterable[Role]] = None,
            default_filter: str = "apply") -> Dict[str, Any]:

        """
        Returns a dictionary with values for the specified `measure_id`.

        `measure_id` -- a measure ID which values should be returned.

        `person_ids` -- list of person IDs to filter result. Only data for
        individuals with person_id in the list `person_ids` are returned.

        `family_ids` -- list of family IDs to filter result. Only data for
        individuals that are members of any of the specified `family_ids`
        are returned.

        `roles` -- list of roles of individuals to select measure value for.
        If not specified value for individuals in all roles are returned.

        `default_filter` -- one of ('`skip`', '`apply`', '`invert`'). When
        the measure has a `default_filter` this argument specifies whether
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
        pass

    def get_values(
            self,
            measure_ids: Iterable[str],
            person_ids: Optional[Iterable[str]] = None,
            family_ids: Optional[Iterable[str]] = None,
            roles: Optional[Iterable[Role]] = None,
            default_filter: str = "apply") -> Dict[str, Dict[str, Any]]:
        """
        Returns dictionary dictionaries with values for all `measure_ids`.

        The returned dictionary uses `person_id` as key. The value for each key
        is a dictionary of measurement values for each ID in `measure_ids`
        keyed measure_id.

        `measure_ids` -- list of measure IDs which values should be returned.

        `person_ids` -- list of person IDs to filter result. Only data for
        individuals with person_id in the list `person_ids` are returned.

        `family_ids` -- list of family IDs to filter result. Only data for
        individuals that are members of any of the specified `family_ids`
        are returned.

        `roles` -- list of roles of individuals to select measure value for.
        If not specified value for individuals in all roles are returned.

        """
        df = self.get_values_df(measure_ids, person_ids, family_ids, roles)
        res = {}
        for row in df.to_dict("records"):
            person_id = row["person_id"]
            res[person_id] = row

        return res

    def get_persons_values_df(
            self,
            measure_ids: Iterable[str],
            person_ids: Optional[List[str]] = None,
            family_ids: Optional[List[str]] = None,
            roles: Optional[List[Role]] = None,
            default_filter: str = "apply") -> pd.DataFrame:
        """
        Returns a data frame with values for all measures in `measure_ids`
        joined with a data frame returned by `get_persons_df`.
        """
        persons_df = self.get_persons_df(
            roles=roles, person_ids=person_ids, family_ids=family_ids)

        value_df = self.get_values_df(
            measure_ids,
            person_ids=person_ids,
            family_ids=family_ids,
            roles=roles,
            default_filter=default_filter)

        df = cast(pd.DataFrame, persons_df.join(
            value_df.set_index("person_id"),
            on="person_id",
            how="right",
            rsuffix="_val"))  # type: ignore
        df = df.set_index("person_id")
        df = df.reset_index()

        return df

    def _get_instrument_measures(self, instrument_name: str) -> List[str]:
        """
        Returns measures for given instrument.
        """
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
            role=None):
        """
        Returns a dataframe with values for all measures in given
        instrument (see **get_values_df**).
        """
        measure_ids = self._get_instrument_measures(instrument_name)
        res = self.get_values_df(measure_ids, person_ids, family_ids, role)
        return res

    def get_instrument_values(
            self, instrument_name,
            person_ids=None,
            family_ids=None,
            role=None):
        """
        Returns a dictionary with values for all measures in given
        instrument (see :func:`get_values`).
        """
        measure_ids = self._get_instrument_measures(instrument_name)
        return self.get_values(measure_ids, person_ids, family_ids, role)


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

    def __init__(self, pheno_id: str, dbfile: str, browser_dbfile: str = None):
        super(PhenotypeStudy, self).__init__(pheno_id)

        self.families = None
        self.db = DbManager(dbfile=dbfile, browser_dbfile=browser_dbfile)
        self.db.build()
        self._load()

    def _get_measures_df(self, instrument=None, measure_type=None):
        """
        Returns data frame containing measures information.

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
        s = select(columns)
        s = s.where(not_(measure.c.measure_type.is_(None)))
        if instrument is not None:
            s = s.where(measure.c.instrument_name == instrument)
        if measure_type is not None:
            s = s.where(measure.c.measure_type == measure_type)

        df = pd.read_sql(s, self.db.pheno_engine)

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
                m = Measure._from_dict(row)
                measures[m.measure_name] = m
                self._measures[m.measure_id] = m
            instrument.measures = measures
            instruments[instrument.instrument_name] = instrument

        self._instruments = instruments

    def _load_families(self):
        families = defaultdict(list)
        persons = self.get_persons()
        for p in list(persons.values()):
            families[p.family_id].append(p)
        self.families = FamiliesData.from_family_persons(families)

    def _load(self):
        """
        Loads basic families, instruments and measures data from
        the phenotype database.
        """
        if not self.families:
            self._load_families()
        if not self.instruments:
            self._load_instruments()

    def get_persons_df(self, roles=None, person_ids=None, family_ids=None):
        """
        Returns a individuals information form phenotype database as a data
        frame.

        `roles` -- specifies persons of which role should be returned. If not
        specified returns all individuals from phenotype database.

        `person_ids` -- list of person IDs to filter result. Only data for
        individuals with person_id in the list `person_ids` are returned.

        `family_ids` -- list of family IDs to filter result. Only data for
        individuals that are members of any of the specified `family_ids`
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
        s = select(columns)
        s = s.select_from(self.db.family.join(self.db.person))
        if roles is not None:
            s = s.where(self.db.person.c.role.in_(roles))
        if person_ids is not None:
            s = s.where(self.db.person.c.person_id.in_(person_ids))
        if family_ids is not None:
            s = s.where(self.db.family.c.family_id.in_(family_ids))
        df = pd.read_sql(s, self.db.pheno_engine)
        # df.rename(columns={'sex': 'sex'}, inplace=True)
        return df[["person_id", "family_id", "role", "sex", "status"]]

    def _build_default_filter_clause(self, m, default_filter):
        if default_filter == "skip" or m.default_filter is None:
            return None
        elif default_filter == "apply":
            return "value {}".format(m.default_filter)
        elif default_filter == "invert":
            return "NOT (value {})".format(m.default_filter)
        else:
            raise ValueError(
                "bad default_filter value: {}".format(default_filter)
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
                "bad measure: {}; unknown value type".format(
                    measure.measure_id
                )
            )
        value_table = self.db.get_value_table(measure_type)
        columns = [
            self.db.family.c.family_id,
            self.db.person.c.person_id,
            self.db.person.c.sex,
            self.db.person.c.status,
            value_table.c.value,
        ]

        s = select(columns)
        s = s.select_from(
            value_table.join(self.db.measure)
            .join(self.db.person)
            .join(self.db.family)
        )
        s = s.where(self.db.measure.c.measure_id == measure.measure_id)

        if roles is not None:
            s = s.where(self.db.person.c.role.in_(roles))
        if person_ids is not None:
            s = s.where(self.db.person.c.person_id.in_(person_ids))
        if family_ids is not None:
            s = s.where(self.db.family.c.family_id.in_(family_ids))

        if measure.default_filter is not None:
            filter_clause = self._build_default_filter_clause(
                measure, default_filter
            )
            if filter_clause is not None:
                s = s.where(text(filter_clause))

        df = pd.read_sql(s, self.db.pheno_engine)
        df.rename(columns={"value": measure.measure_id}, inplace=True)
        return df

    def get_measures_values_streaming_csv(
        self,
        measure_ids,
        person_ids=None,
        family_ids=None,
        roles=None,
        default_filter="apply",
    ):
        columns = [
            self.db.measure.c.measure_id,
            self.db.person.c.person_id,
        ]
        for measure_id in measure_ids:
            assert measure_id in self.measures, measure_id
            measure = self.measures[measure_id]
            measure_type = measure.measure_type
            if measure_type is None:
                raise ValueError(
                    "bad measure: {}; unknown value type".format(
                        measure.measure_id
                    )
                )
        value_tables = [
            self.db.get_value_table(MeasureType.categorical),
            self.db.get_value_table(MeasureType.continuous),
            self.db.get_value_table(MeasureType.ordinal),
            self.db.get_value_table(MeasureType.raw)
        ]

        fieldnames = ["person_id"] + measure_ids

        buffer = StringIO()
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)

        output = dict()

        for vt in value_tables:
            s = select(columns + [vt.c.value])

            j = (
                self.db.family.join(self.db.person)
                .join(vt, isouter=True)
                .join(self.db.measure)
            )

            s = s.select_from(j).where(
                self.db.measure.c.measure_id.in_(measure_ids))

            if roles is not None:
                s = s.where(self.db.person.c.role.in_(roles))
            if person_ids is not None:
                s = s.where(self.db.person.c.person_id.in_(person_ids))
            if family_ids is not None:
                s = s.where(self.db.family.c.family_id.in_(family_ids))

            s = s.order_by(desc(self.db.person.c.person_id))

            with self.db.pheno_engine.connect() as connection:
                results = connection.execute(s)
                for row in results:
                    person_id = row["person_id"]
                    measure_id = row["measure_id"]
                    measure_value = row["value"]

                    if person_id not in output:
                        output[person_id] = {"person_id": person_id}
                        for measure in measure_ids:
                            output[person_id][measure] = "-"

                    output[person_id][measure_id] = measure_value

        for v in output.values():
            writer.writerow(v)
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

    def get_measure_values_df(
        self,
        measure_id,
        person_ids=None,
        family_ids=None,
        roles=None,
        default_filter="apply",
    ):
        """
        Returns a data frame with values for the specified `measure_id`.

        `measure_id` -- a measure ID which values should be returned.

        `person_ids` -- list of person IDs to filter result. Only data for
        individuals with person_id in the list `person_ids` are returned.

        `family_ids` -- list of family IDs to filter result. Only data for
        individuals that are members of any of the specified `family_ids`
        are returned.

        `roles` -- list of roles of individuals to select measure value for.
        If not specified value for individuals in all roles are retuned.

        `default_filter` -- one of ('`skip`', '`apply`', '`invert`'). When
        the measure has a `default_filter` this argument specifies whether
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
        default_filter="apply",
    ):
        """
        Returns a data frame with values for given list of measures.

        Values are loaded using consecutive calls to
        `get_measure_values_df()` method for each measure in `measure_ids`.
        All data frames are joined in the end and returned.

        `measure_ids` -- list of measure ids which values should be returned.

        `person_ids` -- list of person IDs to filter result. Only data for
        individuals with person_id in the list `person_ids` are returned.

        `family_ids` -- list of family IDs to filter result. Only data for
        individuals that are members of any of the specified `family_ids`
        are returned.

        `roles` -- list of roles of individuals to select measure value for.
        If not specified value for individuals in all roles are returned.
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
                rsuffix="_val_{}".format(i),
            )

        return res_df

    def get_values_streaming_csv(
        self,
        measure_ids,
        person_ids=None,
        family_ids=None,
        roles=None,
        default_filter="apply",
    ):
        """
        Returns a data frame with values for given list of measures.

        Values are loaded using consecutive calls to
        `get_measure_values_df()` method for each measure in `measure_ids`.
        All data frames are joined in the end and returned.

        `measure_ids` -- list of measure ids which values should be returned.

        `person_ids` -- list of person IDs to filter result. Only data for
        individuals with person_id in the list `person_ids` are returned.

        `family_ids` -- list of family IDs to filter result. Only data for
        individuals that are members of any of the specified `family_ids`
        are returned.

        `roles` -- list of roles of individuals to select measure value for.
        If not specified value for individuals in all roles are returned.
        """
        assert isinstance(measure_ids, list)
        assert len(measure_ids) >= 1
        assert all([self.has_measure(m) for m in measure_ids])

        return self.get_measures_values_streaming_csv(
            measure_ids, person_ids, family_ids, roles, default_filter
        )

    def get_regressions(self):
        return self.db.regression_display_names_with_ids

    def get_measures_info(self):
        return {
            "base_image_url": get_pheno_base_url(),
            "has_descriptions": self.db.has_descriptions,
            "regression_names": self.db.regression_display_names,
        }

    def search_measures(self, instrument, search_term):
        measures = self.db.search_measures(instrument, search_term)

        for m in measures:
            if m["values_domain"] is None:
                m["values_domain"] = ""
            m["measure_type"] = m["measure_type"].name

            m["regressions"] = []
            regressions = self.db.get_regression_values(m["measure_id"]) or []

            for reg in regressions:
                reg = dict(reg)
                if isnan(reg["pvalue_regression_male"]):
                    reg["pvalue_regression_male"] = "NaN"
                if isnan(reg["pvalue_regression_female"]):
                    reg["pvalue_regression_female"] = "NaN"
                m["regressions"].append(reg)

            yield {
                "measure": m,
            }


class PhenotypeGroup(PhenotypeData):

    def __init__(self, pheno_id: str, phenotype_data: Iterable[PhenotypeData]):
        super(PhenotypeGroup, self).__init__(pheno_id)
        self.phenotype_datas = phenotype_data
        self.families = FamiliesData.combine_studies(self.phenotype_datas)
        instruments, measures = self._merge_instruments(
            [ph.instruments for ph in self.phenotype_datas])
        self._instruments.update(instruments)

        self._measures.update(measures)

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
                        logger.warn(
                            f"{full_name} measure duplication! ignoring"
                        )
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
        #             assert group_instrument.instrument_name == instrument_name

        #             measure_ids = set(instrument.keys())
        #             group_measure_ids = set(group_instrument.measures.keys())

        #             if measure_ids & group_measure_ids:
        #                 msg = f"can't merge instruments because of measures " \
        #                     f"{measure_ids & group_measure_ids}"
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

        ped_df = self.families.ped_df[[
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
        for pheno in self.phenotype_datas:
            if pheno.has_measure(measure_id):
                return pheno.get_measure_values_df(
                    measure_id,
                    person_ids=person_ids,
                    family_ids=family_ids,
                    roles=roles,
                    default_filter=default_filter
                )

        # We should never get here
        msg = f"measure {measure_id} not found in phenotype group {self.id}"
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
        for pheno in self.phenotype_datas:
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
            res_df = cast(pd.DataFrame, res_df.join(
                df.set_index("person_id"),
                on="person_id",
                how="outer",
                rsuffix="_val_{}".format(i),
            ))  # type: ignore

        return res_df

    def get_regressions(self):
        res = []
        for pheno in self.phenotype_datas:
            res += pheno.get_regressions()
        return res

    def get_measures_info(self):
        result = {
            "base_image_url": get_pheno_base_url(),
            "has_descriptions": False,
            "regression_names": dict()
        }
        for pheno in self.phenotype_datas:
            measures_info = pheno.get_measures_info()
            result["has_descriptions"] = \
                result["has_descriptions"] or measures_info["has_descriptions"]
            result["regression_names"].update(
                measures_info["regression_names"]
            )
        return result

    def search_measures(self, instrument, search_term):
        generators = [
            pheno.search_measures(instrument, search_term)
            for pheno in self.phenotype_datas
        ]
        measures = chain(*generators)
        for m in measures:
            yield m


class PhenoDb(object):
    def __init__(self, dae_config):
        super(PhenoDb, self).__init__()
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

        self.pheno_cache = {}

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

    def get_phenotype_data(self, pheno_id):
        if not self.has_phenotype_data(pheno_id):
            return None
        if pheno_id in self.pheno_cache:
            phenotype_data = self.pheno_cache[pheno_id]
        else:
            config = self.get_dbconfig(pheno_id)
            if config.phenotype_data_list is not None:
                logger.info(f"loading pheno db group <{pheno_id}>")
                phenotype_studies = [
                    self.get_phenotype_data(ps_id)
                    for ps_id in config.phenotype_data_list
                ]
                phenotype_data = PhenotypeGroup(pheno_id, phenotype_studies)
            else:
                logger.info(f"loading pheno db <{pheno_id}>")
                phenotype_data = PhenotypeStudy(
                    pheno_id,
                    dbfile=self.get_dbfile(pheno_id),
                    browser_dbfile=self.get_browser_dbfile(pheno_id)
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
