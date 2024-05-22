import os
from collections.abc import Iterator
from typing import Any, Optional, Union

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
from dae.utils.progress import progress, progress_nl
from dae.variants.attributes import Role

mpl.use("PS")
plt.ioff()


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

    def _augment_measure_values_df(
        self, augment: Measure, augment_name: str,
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
        if not self.phenotype_data.has_measure(augment_id):
            return None

        df = self.phenotype_data.get_people_measure_values_df(
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

    def figure_filepath(self, measure: Measure, suffix: str) -> str:
        """Construct file path for storing a measure figures."""
        filename = f"{measure.measure_id}.{suffix}.png"

        assert measure.instrument_name is not None
        outdir = os.path.join(
            self.images_dir,
            self.phenotype_data.pheno_id,
            measure.instrument_name,
        )
        if not os.path.exists(outdir):
            os.makedirs(outdir, exist_ok=True)

        filepath = os.path.join(outdir, filename)
        return filepath

    def browsable_figure_path(self, measure: Measure, suffix: str) -> str:
        """Construct file path for storing a measure figures."""
        filename = f"{measure.measure_id}.{suffix}.png"
        assert measure.instrument_name is not None
        filepath = os.path.join(
            self.phenotype_data.pheno_id,
            measure.instrument_name,
            filename,
        )
        return filepath

    def save_fig(
        self, measure: Measure, suffix: str,
    ) -> tuple[Optional[str], Optional[str]]:
        """Save measure figures."""
        if "/" in measure.measure_id:
            return (None, None)

        small_filepath = self.figure_filepath(
            measure, f"{suffix}_small",
        )
        plt.savefig(small_filepath, dpi=self.SMALL_DPI)

        filepath = self.figure_filepath(measure, suffix)
        plt.savefig(filepath, dpi=self.LARGE_DPI)
        plt.close()
        return (
            self.browsable_figure_path(measure, f"{suffix}_small"),
            self.browsable_figure_path(measure, suffix),
        )

    def build_regression(
        self, dependent_measure: Measure,
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

        aug_df = self._augment_measure_values_df(
            independent_measure, aug_col_name, dependent_measure,
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
            ) = self.save_fig(
                dependent_measure, f"prb_regression_by_{aug_col_name}",
            )
        return res

    def build_values_violinplot(self, measure: Measure) -> dict[str, Any]:
        """Build a violin plot figure for the measure."""
        df = self.load_measure(measure)
        drawn = draw_measure_violinplot(df.dropna(), measure.measure_id)

        res = {}

        if drawn:
            (
                res["figure_distribution_small"],
                res["figure_distribution"],
            ) = self.save_fig(measure, "violinplot")

        return res

    def build_values_categorical_distribution(
        self, measure: Measure,
    ) -> dict[str, Any]:
        """Build a categorical value distribution fiugre."""
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

    def build_values_ordinal_distribution(
        self, measure: Measure,
    ) -> dict[str, Any]:
        """Build an ordinal value distribution figure."""
        df = self.load_measure(measure)
        drawn = draw_ordinal_violin_distribution(
            df.dropna(), measure.measure_id,
        )

        res = {}
        if drawn:
            (
                res["figure_distribution_small"],
                res["figure_distribution"],
            ) = self.save_fig(measure, "distribution")

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

    def handle_measure(self, measure: Measure) -> dict[str, Any]:
        """Build appropriate figures for a measure."""
        res = PreparePhenoBrowserBase._measure_to_dict(measure)

        if measure.measure_type == MeasureType.continuous:
            res.update(self.build_values_violinplot(measure))
        elif measure.measure_type == MeasureType.ordinal:
            res.update(self.build_values_ordinal_distribution(measure))
        elif measure.measure_type == MeasureType.categorical:
            res.update(self.build_values_categorical_distribution(measure))

        return res

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

    def handle_regressions(
        self, measure: Measure,
    ) -> Iterator[dict[str, Any]]:
        """Build appropriate regressions and regression figures."""
        if measure.measure_type not in [
            MeasureType.continuous,
            MeasureType.ordinal,
        ]:
            return
        if self.pheno_regressions is None or \
                self.pheno_regressions.regression is None:
            return
        for reg_id, reg in self.pheno_regressions.regression.items():
            res = {"measure_id": measure.measure_id}
            measure_names = reg.measure_names
            if measure_names is None:
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

            res["regression_id"] = reg_id
            regression = self.build_regression(
                measure, reg_measure, reg.jitter,
            )
            res.update(regression)  # type: ignore
            if (
                res.get("pvalue_regression_male") is not None
                or res.get("pvalue_regression_female") is not None
            ):
                yield res

    def run(self) -> None:
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

        for instrument in list(self.phenotype_data.instruments.values()):
            progress_nl()
            for measure in list(instrument.measures.values()):
                progress(text=str(measure) + "\n")
                var = self.handle_measure(measure)
                db.save(var)
                if self.pheno_regressions:
                    for regression in self.handle_regressions(measure):
                        db.save_regression_values(regression)
