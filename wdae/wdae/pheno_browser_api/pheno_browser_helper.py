import csv
import logging
from abc import abstractmethod
from collections.abc import Generator
from io import StringIO
from typing import Any

from gpf_instance.extension import GPFTool
from studies.study_wrapper import WDAEAbstractStudy, WDAEStudy

logger = logging.getLogger(__name__)


class CountError(Exception):
    pass


class BasePhenoBrowserHelper(GPFTool):
    """Base class for pheno browser helpers."""

    def __init__(self) -> None:
        super().__init__("pheno_browser_helper")

    @abstractmethod
    def get_instruments(self) -> list[str]:
        """Get instruments."""

    @abstractmethod
    def get_measures_info(self) -> dict[str, Any]:
        """Get measures info."""

    @abstractmethod
    def get_measure_description(self, measure_id: str) -> dict[str, Any]:
        """Get measures description."""

    @abstractmethod
    def search_measures(
        self,
        data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Search measures."""

    @abstractmethod
    def get_measure_ids(
        self,
        data: dict[str, Any],
    ) -> Generator[str, None, None]:
        """Get measure ids."""

    @abstractmethod
    def measures_count_status(
        self,
        data: dict[str, Any],
    ) -> str:
        """Get measure ids count status."""

    @abstractmethod
    def get_count(self, data: dict[str, Any]) -> int:
        """Return measure count for request."""

    @abstractmethod
    def get_image(self, image_path: str) -> tuple[bytes | None, str | None]:
        """Get image by path."""


class PhenoBrowserHelper(BasePhenoBrowserHelper):
    """Build enrichment tool test."""

    def __init__(
        self,
        study: WDAEStudy,
    ) -> None:
        super().__init__()
        self.study = study

    @staticmethod
    def make_tool(study: WDAEAbstractStudy) -> GPFTool | None:
        raise NotImplementedError

    def get_instruments(self) -> list[str]:
        if not self.study.has_pheno_data:
            raise ValueError(
                f"Study {self.study.study_id} has no phenotype data.",
            )
        return sorted(self.study.phenotype_data.get_instruments())

    def get_measures_info(self) -> dict[str, Any]:
        if not self.study.has_pheno_data:
            raise ValueError(
                f"Study {self.study.study_id} has no phenotype data.",
            )
        return self.study.phenotype_data.get_measures_info()

    def get_measure_description(self, measure_id: str) -> dict[str, Any]:
        if not self.study.has_pheno_data:
            raise ValueError(
                f"Study {self.study.study_id} has no phenotype data.",
            )
        if not self.study.phenotype_data.has_measure(measure_id):
            raise KeyError(
                f"Study {self.study.study_id} phenotype data "
                f"has no measure with id {measure_id}",
            )
        return self.study.phenotype_data.get_measure_description(measure_id)

    def search_measures(
        self,
        data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if not self.study.has_pheno_data:
            raise ValueError(
                f"Study {self.study.study_id} has no phenotype data.",
            )

        instrument = data.get("instrument")
        search_term = data.get("search")

        pheno_instruments = self.get_instruments()

        if instrument and instrument not in pheno_instruments:
            raise KeyError(
                f"Instrument {instrument} not found in study "
                f"{self.study.study_id} phenotype data.",
            )

        measures = self.study.phenotype_data.search_measures(
            instrument,
            search_term,
        )

        return list(measures)

    def get_measure_ids(
        self,
        data: dict[str, Any],
      ) -> Generator[str, None, None]:
        data = {k: str(v) for k, v in data.items()}

        if not self.study.has_pheno_data:
            raise KeyError

        search_term = data.get("search_term")
        instrument = data.get("instrument")

        if (instrument is not None
                and instrument != ""
                and instrument not in self.study.phenotype_data.instruments):
            raise KeyError

        measures = self.study.phenotype_data.search_measures(
            instrument, search_term,
        )
        measure_ids = [
            measure["measure"]["measure_id"] for measure in measures
        ]

        if len(measure_ids) > 1900:
            raise CountError

        return self._csv_value_iterator(
            self.study, measure_ids,
        )

    def _csv_value_iterator(
        self,
        dataset: WDAEStudy,
        measure_ids: list[str],
    ) -> Generator[str, None, None]:
        """Create CSV content for people measures data."""
        header = ["person_id", *measure_ids]
        buffer = StringIO()
        writer = csv.writer(buffer, delimiter=",")
        writer.writerow(header)
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)

        values_iterator = dataset.phenotype_data.get_people_measure_values(
            measure_ids)

        for values_dict in values_iterator:
            output = [values_dict[header[0]]]
            all_null = True
            for col in header[1:]:
                value = values_dict[col]
                if value is not None:
                    all_null = False
                output.append(value)
            if all_null:
                continue
            writer.writerow(output)
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

        buffer.close()

    def measures_count_status(
        self,
        data: dict[str, Any],
    ) -> str:
        count = self._count_measure_ids(data)

        if count > 1900:
            return "too large"
        if count == 0:
            return "zero"
        return "ok"

    def _count_measure_ids(self, data: dict[str, Any]) -> int:
        data = {k: str(v) for k, v in data.items()}

        if not self.study.has_pheno_data:
            raise KeyError

        search_term = data.get("search_term")
        instrument = data.get("instrument")

        if (instrument is not None
                and instrument != ""
                and instrument not in self.study.phenotype_data.instruments):
            raise KeyError

        return self.study.phenotype_data.count_measures(
            instrument, search_term,
        )

    def get_count(self, data: dict[str, Any]) -> int:
        data = {k: str(v) for k, v in data.items()}

        if not self.study or not self.study.has_pheno_data:
            raise KeyError

        search_term = data.get("search_term")
        instrument = data.get("instrument")

        if (instrument is not None
                and instrument != ""
                and instrument not in self.study.phenotype_data.instruments):
            raise KeyError

        return self.study.phenotype_data.count_measures(
            instrument, search_term,
        )

    def get_image(self, image_path: str) -> tuple[bytes | None, str | None]:
        if not self.study.has_pheno_data:
            raise KeyError
        return self.study.phenotype_data.get_image(image_path)
