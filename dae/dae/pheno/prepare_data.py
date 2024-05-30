import os
from collections.abc import Iterator
from typing import Any, Optional, Union
import logging
import shutil
import tempfile

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from box import Box

from dae.pheno.common import MeasureType
from dae.pheno.graphs import (
    draw_categorical_violin_distribution,
    draw_linregres,
    draw_measure_violinplot,
    draw_ordinal_violin_distribution,
)
from dae.pheno.pheno_data import (
    Measure,
    PhenotypeStudy,
    get_pheno_browser_images_dir,
)
from dae.pheno.db import PhenoDb

from dae.task_graph.graph import Task, TaskGraph
from dae.task_graph.executor import task_graph_run_with_results
from dae.task_graph.cli_tools import TaskGraphCli, TaskCache

from dae.utils.progress import progress, progress_nl
from dae.variants.attributes import Role
from sqlalchemy import text

mpl.use("PS")
plt.ioff()

logger = logging.getLogger(__name__)


class PreparePhenoBrowserBase:
    """Prepares phenotype data for the phenotype browser."""

    LARGE_DPI = 150
    SMALL_DPI = 16

    def __init__(
        self,
        pheno_name: str,
        phenotype_data: PhenotypeStudy,
        output_dir: str,
        pheno_regressions: Optional[Box] = None,
        images_dir: Optional[str] = None,
    ) -> None:
        assert os.path.exists(output_dir)
        self.output_dir = output_dir
        if images_dir is None:
            images_dir = get_pheno_browser_images_dir()
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)

        assert os.path.exists(images_dir)

        self.pheno_id = pheno_name

        self.images_dir = images_dir

        self.phenotype_data = phenotype_data
        self.pheno_regressions = pheno_regressions
        if self.pheno_regressions is not None:
            for reg_data in self.pheno_regressions.regression.values():
                if "measure_names" in reg_data:
                    reg_data["measure_name"] = reg_data["measure_names"][0]

    def load_measure(self, measure: Measure) -> pd.DataFrame:
        df = self.phenotype_data.get_people_measure_values_df(
            [measure.measure_id],
        )
        return df

    @staticmethod
    def _augment_measure_values_df(
        phenotype_data: PhenotypeStudy,
        augment: Measure, augment_name: str,
        measure: Measure,
    ) -> Optional[pd.DataFrame]:
        assert augment is not None
        assert isinstance(augment, Measure)

        augment_instrument = augment.instrument_name
        augment_measure = augment.measure_name

        if augment_instrument is not None:
            augment_id = f"{augment_instrument}.{augment_measure}"
        else:
            augment_id = f"{measure.instrument_name}.{augment_measure}"

        if augment_id == measure.measure_id:
            return None
        if not phenotype_data.has_measure(augment_id):
            return None

        df = phenotype_data.get_people_measure_values_df(
            [augment_id, measure.measure_id],
        )
        df.loc[df.role == Role.mom, "role"] = Role.parent  # type: ignore
        df.loc[df.role == Role.dad, "role"] = Role.parent  # type: ignore

        df.rename(columns={augment_id: augment_name}, inplace=True)
        return df

    @staticmethod
    def _measure_to_dict(measure: Measure) -> dict[str, Any]:
        return {
            "measure_id": measure.measure_id,
            "instrument_name": measure.instrument_name,
            "measure_name": measure.measure_name,
            "measure_type": measure.measure_type.value,
            "description": measure.description,
            "values_domain": measure.values_domain,
        }

    @classmethod
    def figure_filepath(
        cls, pheno_id: str, images_dir: str, measure: Measure, suffix: str
    ) -> str:
        """Construct file path for storing a measure figures."""
        filename = f"{measure.measure_id}.{suffix}.png"

        assert measure.instrument_name is not None
        outdir = os.path.join(
            images_dir,
            pheno_id,
            measure.instrument_name,
        )
        if not os.path.exists(outdir):
            os.makedirs(outdir, exist_ok=True)

        filepath = os.path.join(outdir, filename)
        return filepath

    @classmethod
    def browsable_figure_path(
        cls, pheno_id: str, measure: Measure, suffix: str
    ) -> str:
        """Construct file path for storing a measure figures."""
        filename = f"{measure.measure_id}.{suffix}.png"
        assert measure.instrument_name is not None
        filepath = os.path.join(
            pheno_id,
            measure.instrument_name,
            filename,
        )
        return filepath

    @classmethod
    def save_fig(
            cls, pheno_id: str, images_dir: str, measure: Measure, suffix: str,
    ) -> tuple[Optional[str], Optional[str]]:
        """Save measure figures."""
        if "/" in measure.measure_id:
            return (None, None)

        small_filepath = cls.figure_filepath(
            pheno_id, images_dir, measure, f"{suffix}_small",
        )
        plt.savefig(small_filepath, dpi=cls.SMALL_DPI)

        filepath = cls.figure_filepath(pheno_id, images_dir, measure, suffix)
        plt.savefig(filepath, dpi=cls.LARGE_DPI)
        plt.close()
        return (
            cls.browsable_figure_path(pheno_id, measure, f"{suffix}_small"),
            cls.browsable_figure_path(pheno_id, measure, suffix),
        )

    @classmethod
    def build_regression(
        cls,
        phenotype_data: PhenotypeStudy,
        images_dir: str,
        dependent_measure: Measure,
        independent_measure: Measure,
        jitter: float,
    ) -> dict[str, Union[str, float]]:
        """Build measure regressiongs."""
        min_number_of_values = 5
        min_number_of_unique_values = 2

        res: dict[str, Any] = {}

        if dependent_measure.measure_id == independent_measure.measure_id:
            return res

        aug_col_name = independent_measure.measure_name

        aug_df = cls._augment_measure_values_df(
            phenotype_data, independent_measure,
            aug_col_name, dependent_measure,
        )

        if aug_df is None:
            return res

        assert aug_df is not None
        aug_df = aug_df[aug_df.role == Role.prb]
        aug_df.loc[:, aug_col_name] = aug_df[aug_col_name].astype(np.float32)
        aug_df = aug_df[np.isfinite(aug_df[aug_col_name])]

        assert aug_df is not None
        if (
            aug_df[dependent_measure.measure_id].nunique()
            < min_number_of_unique_values
            or len(aug_df) <= min_number_of_values
        ):
            return res

        res_male, res_female = draw_linregres(
            aug_df, aug_col_name, dependent_measure.measure_id,
            jitter,  # type: ignore
        )
        res["pvalue_regression_male"] = (
            res_male.pvalues[1] if res_male is not None else None
        )
        res["pvalue_regression_female"] = (
            res_female.pvalues[1]
            if res_female is not None
            else None
        )

        if res_male is not None or res_female is not None:
            (
                res["figure_regression_small"],
                res["figure_regression"],
            ) = cls.save_fig(
                phenotype_data.pheno_id, images_dir,
                dependent_measure, f"prb_regression_by_{aug_col_name}"
            )
        return res

    @classmethod
    def build_values_violinplot(
        cls, pheno_id: str, images_dir: str,
        df: pd.DataFrame, measure: Measure,
    ) -> dict[str, Any]:
        """Build a violin plot figure for the measure."""
        drawn = draw_measure_violinplot(df.dropna(), measure.measure_id)

        res = {}

        if drawn:
            (
                res["figure_distribution_small"],
                res["figure_distribution"],
            ) = cls.save_fig(pheno_id, images_dir, measure, "violinplot")

        return res

    @classmethod
    def build_values_categorical_distribution(
        cls, pheno_id: str, images_dir: str,
        df: pd.DataFrame, measure: Measure,
    ) -> dict[str, Any]:
        """Build a categorical value distribution fiugre."""
        drawn = draw_categorical_violin_distribution(
            df.dropna(), measure.measure_id,
        )

        res = {}
        if drawn:
            (
                res["figure_distribution_small"],
                res["figure_distribution"],
            ) = cls.save_fig(pheno_id, images_dir, measure, "distribution")

        return res

    def build_values_other_distribution(
        self, measure: Measure,
    ) -> dict[str, Any]:
        """Build an other value distribution figure."""
        df = self.load_measure(measure)
        drawn = draw_categorical_violin_distribution(
            df.dropna(), measure.measure_id,
        )

        res = {}
        if drawn:
            (
                res["figure_distribution_small"],
                res["figure_distribution"],
            ) = self.save_fig(measure, "distribution")

        return res

    @classmethod
    def build_values_ordinal_distribution(
        cls, pheno_id: str, images_dir: str,
        df: pd.DataFrame, measure: Measure,
    ) -> dict[str, Any]:
        """Build an ordinal value distribution figure."""
        drawn = draw_ordinal_violin_distribution(
            df.dropna(), measure.measure_id,
        )

        res = {}
        if drawn:
            (
                res["figure_distribution_small"],
                res["figure_distribution"],
            ) = cls.save_fig(pheno_id, images_dir, measure, "distribution")

        return res

    def dump_browser_variable(self, var: dict[str, Any]) -> None:
        """Print browser measure description."""
        print("-------------------------------------------")
        print(var["measure_id"])
        print("-------------------------------------------")
        print(f"instrument:  {var['instrument_name']}")
        print(f"measure:     {var['measure_name']}")
        print(f"type:        {var['measure_type']}")
        print(f"description: {var['description']}")
        print(f"domain:      {var['values_domain']}")
        print("-------------------------------------------")

    def _get_measure_by_name(
        self, measure_name: str, instrument_name: str,
    ) -> Optional[Measure]:
        if instrument_name:
            measure_id = ".".join([instrument_name, measure_name])
            if self.phenotype_data.has_measure(measure_id):
                return self.phenotype_data.get_measure(measure_id)
        return None

    def _has_regression_measure(
        self, measure_name: str,
        instrument_name: Optional[str],
    ) -> bool:
        if self.pheno_regressions is None or \
                self.pheno_regressions.regression is None:
            return False

        for reg in self.pheno_regressions.regression.values():
            if measure_name == reg.measure_name:
                if (
                    instrument_name
                    and reg.instrument_name
                    and instrument_name != reg.instrument_name
                ):
                    continue
                return True
        return False

    def run(self, **kwargs) -> None:
        """Run browser preparations for all measures in a phenotype data."""
        db = self.phenotype_data.db

        if self.pheno_regressions:
            for reg_id, reg_data in self.pheno_regressions.regression.items():
                db.save_regression(
                    {
                        "regression_id": reg_id,
                        "instrument_name": reg_data.instrument_name,
                        "measure_name": reg_data.measure_name,
                        "display_name": reg_data.display_name,
                    },
                )
        with db.engine.begin() as conn:
            conn.execute(text("CHECKPOINT"))

        graph = TaskGraph()

        with tempfile.NamedTemporaryFile() as temp_dbfile:
            shutil.copyfile(db.dbfile, temp_dbfile.name)
            for instrument in list(self.phenotype_data.instruments.values()):
                for measure in list(instrument.measures.values()):
                    self.add_measure_task(graph, measure, temp_dbfile.name)
            task_cache = TaskCache.create(
                force=False, cache_dir=kwargs.get("task_status_dir"))
            with TaskGraphCli.create_executor(task_cache, **kwargs) as xtor:
                try:
                    for result in task_graph_run_with_results(graph, xtor):
                        measure, regressions = result
                        db.save(measure)
                        if regressions is None:
                            continue
                        for regression in regressions:
                            db.save_regression_values(regression)
                except Exception:
                    logger.exception("Failed to create images")

    def add_measure_task(
            self, graph: TaskGraph, measure: Measure, dbfile: str
    ) -> None:
        regression_measures: dict[str, tuple[Box, pd.DataFrame]] = {}
        for reg_id, reg in self.pheno_regressions.regression.items():
            measure_names = reg.measure_names
            if measure_names is None:
                assert reg.measure_name is not None
                measure_names = [reg.measure_name]
            for measure_name in measure_names:
                reg_measure = self._get_measure_by_name(
                    measure_name,
                    reg.instrument_name
                    or measure.instrument_name,  # type: ignore
                )
                if not reg_measure:
                    continue
                else:
                    break
            if not reg_measure:
                continue
            if self._has_regression_measure(
                measure.measure_name, measure.instrument_name,
            ):
                continue
            regression_measures[reg_id] = (reg, reg_measure)

        graph.create_task(
            f"build_{measure.measure_id}",
            PreparePhenoBrowserBase.do_measure_build,
            [
                self.pheno_id,
                dbfile,
                self.phenotype_data.config,
                measure,
                self.images_dir,
                regression_measures
            ],
            []
        )

    @classmethod
    def do_measure_build(
        cls,
        pheno_id: str,
        dbfile: str,
        db_config: Optional[Box],
        measure: Measure,
        images_dir: str,
        regression_measures: dict[str, tuple[Box, Measure]]
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        pheno_data = PhenotypeStudy(
            pheno_id, dbfile, db_config, read_only=True
        )
        df = pheno_data.get_people_measure_values_df(
            [measure.measure_id],
        )
        measure_dict = PreparePhenoBrowserBase._measure_to_dict(measure)
        if measure.measure_type == MeasureType.continuous:
            measure_dict.update(cls.build_values_violinplot(
                pheno_id, images_dir, df, measure
            ))
        elif measure.measure_type == MeasureType.ordinal:
            measure_dict.update(cls.build_values_ordinal_distribution(
                pheno_id, images_dir, df, measure
            ))
        elif measure.measure_type == MeasureType.categorical:
            measure_dict.update(cls.build_values_categorical_distribution(
                pheno_id, images_dir, df, measure
            ))

        if len(regression_measures) == 0:
            return measure_dict, None

        if measure.measure_type not in [
            MeasureType.continuous,
            MeasureType.ordinal,
        ]:
            return measure_dict, None

        regression_rows = []
        for reg_id, reg_conf_and_measure in regression_measures.items():
            reg_conf, reg_measure = reg_conf_and_measure
            res = {
                "measure_id": measure.measure_id,
                "regression_id": reg_id
            }
            regression = cls.build_regression(
                pheno_data, images_dir, measure, reg_measure, reg_conf.jitter,
            )
            res.update(regression)  # type: ignore
            if (
                res.get("pvalue_regression_male") is not None
                or res.get("pvalue_regression_female") is not None
            ):
                regression_rows.append(res)

        return measure_dict, regression_rows
