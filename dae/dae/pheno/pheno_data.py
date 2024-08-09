# pylint: disable=too-many-lines
from __future__ import annotations

import logging
import math
import os
from abc import ABC, abstractmethod
from collections.abc import Generator, Iterable, Sequence
from itertools import chain
from typing import Any, cast

import pandas as pd
from box import Box

from dae.pheno.common import MeasureType
from dae.pheno.db import PhenoDb
from dae.utils.helpers import isnan
from dae.variants.attributes import Role

logger = logging.getLogger(__name__)


def get_pheno_db_dir(dae_config: Box | None) -> str:
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


def get_pheno_browser_images_dir(dae_config: Box | None = None) -> str:
    """Get images directory for pheno DB."""
    pheno_db_dir = os.environ.get(
        "DAE_PHENODB_DIR",
        get_pheno_db_dir(dae_config),
    )
    browser_images_path = os.path.join(pheno_db_dir, "images")
    if not os.path.exists(browser_images_path):
        logger.error(
            "Pheno images path %s does not exist!", browser_images_path,
        )
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

    def __init__(self, pheno_id: str, config: Box | None) -> None:
        self._pheno_id: str = pheno_id
        self.config = config
        self._measures: dict[str, Measure] = {}
        self._instruments: dict[str, Instrument] = {}

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
    def search_measures(
        self,
        instrument: str | None,
        search_term: str | None,
        page: int | None = None,
        sort_by: str | None = None,
        order_by:  str | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """Yield measures in the DB according to filters."""

    def has_measure(self, measure_id: str) -> bool:
        """Check if phenotype DB contains a measure by ID."""
        return measure_id in self._measures

    def get_measure(self, measure_id: str) -> Measure:
        """Return a measure by measure_id."""
        assert measure_id in self._measures, measure_id
        return self._measures[measure_id]

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
            config: Box | None = None, *, read_only: bool = True) -> None:
        super().__init__(pheno_id, config)

        self.db = PhenoDb(dbfile, read_only=read_only)
        self.config = config
        df = self._get_measures_df()
        self._instruments = self._load_instruments(df)
        logger.warning("phenotype study %s fully loaded", pheno_id)

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

    def _build_default_filter_clause(
        self, measure: Measure, default_filter: str,
    ) -> str | None:
        if default_filter == "skip" or measure.default_filter is None:
            return None
        if default_filter == "apply":
            return f"value {measure.default_filter}"
        if default_filter == "invert":
            return f"NOT (value {measure.default_filter})"

        raise ValueError(
            f"bad default_filter value: {default_filter}",
        )

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
        return self.db.regression_display_names_with_ids

    def get_regression_ids(self) -> list[str]:
        return self.db.regression_ids

    def _get_pheno_images_base_url(self) -> str | None:
        return None if self.config is None \
            else self.config.get("browser_images_url")

    def get_measures_info(self) -> dict[str, Any]:
        return {
            "base_image_url": self._get_pheno_images_base_url(),
            "has_descriptions": self.db.has_descriptions,
            "regression_names": self.db.regression_display_names,
        }

    def search_measures(
        self,
        instrument: str | None,
        search_term: str | None,
        page: int | None = None,
        sort_by: str | None = None,
        order_by:  str | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        measures = self.db.search_measures(
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
            for reg_id in self.get_regression_ids():
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


class PhenotypeGroup(PhenotypeData):
    """Represents a group of phenotype data studies or groups."""

    def __init__(
        self, pheno_id: str, children: list[PhenotypeData],
    ) -> None:
        super().__init__(pheno_id, None)
        self.children = children
        instruments, measures = self._merge_instruments(
            [ph.instruments for ph in self.children])
        self._instruments.update(instruments)

        self._measures.update(measures)

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
        order_by:  str | None = None,
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
        measures = chain(*generators)
        yield from measures

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
        dfs: list[pd.DataFrame] = []
        for child in self.children:
            measures_in_child = list(
                filter(child.has_measure, measure_ids))
            if len(measures_in_child) > 0:
                dfs.append(child.get_people_measure_values_df(
                    measures_in_child,
                    person_ids,
                    family_ids,
                    roles,
                ))
        return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
