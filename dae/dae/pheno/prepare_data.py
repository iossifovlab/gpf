"""
Created on Apr 10, 2017

@author: lubo
"""
import os
import matplotlib as mpl

import numpy as np

from dae.pheno.pheno_db import Measure, get_pheno_browser_images_dir

import matplotlib.pyplot as plt

from dae.pheno.db import DbManager
from dae.pheno.common import Role, MeasureType

from dae.pheno.graphs import draw_linregres
from dae.pheno.graphs import draw_measure_violinplot
from dae.pheno.graphs import draw_categorical_violin_distribution
from dae.pheno.graphs import draw_ordinal_violin_distribution
from dae.utils.progress import progress, progress_nl


mpl.use("PS")
plt.ioff()  # type: ignore


class PreparePhenoBrowserBase(object):

    LARGE_DPI = 150
    SMALL_DPI = 16

    def __init__(
        self,
        pheno_name,
        phenotype_data,
        output_dir,
        pheno_regressions=None,
        images_dir=None,
    ):
        assert os.path.exists(output_dir)
        self.output_dir = output_dir
        if images_dir is None:
            images_dir = get_pheno_browser_images_dir()
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)

        assert os.path.exists(images_dir)

        self.images_dir = images_dir

        self.phenotype_data = phenotype_data
        self.pheno_regressions = pheno_regressions

        self.browser_db = os.path.join(
            output_dir, "{}_browser.db".format(pheno_name)
        )

    def load_measure(self, measure):
        df = self.phenotype_data.get_persons_values_df([measure.measure_id])
        return df

    def _augment_measure_values_df(self, augment, augment_name, measure):
        assert augment is not None
        assert isinstance(augment, Measure)

        augment_instrument = augment.instrument_name
        augment_measure = augment.measure_name

        if augment_instrument is not None:
            augment_id = "{}.{}".format(augment_instrument, augment_measure)
        else:
            augment_id = "{}.{}".format(
                measure.instrument_name, augment_measure
            )

        if augment_id == measure.measure_id:
            return None
        if not self.phenotype_data.has_measure(augment_id):
            return None

        df = self.phenotype_data.get_persons_values_df(
            [augment_id, measure.measure_id]
        )
        df.loc[df.role == Role.mom, "role"] = Role.parent
        df.loc[df.role == Role.dad, "role"] = Role.parent

        df.rename(columns={augment_id: augment_name}, inplace=True)
        return df

    @staticmethod
    def _measure_to_dict(measure):
        return {
            "measure_id": measure.measure_id,
            "instrument_name": measure.instrument_name,
            "measure_name": measure.measure_name,
            "measure_type": measure.measure_type,
            "description": measure.description,
            "values_domain": measure.values_domain,
        }

    def figure_filepath(self, measure, suffix):
        filename = "{}.{}.png".format(measure.measure_id, suffix)
        outdir = os.path.join(
            self.images_dir,
            self.phenotype_data.pheno_id,
            measure.instrument_name
        )
        if not os.path.exists(outdir):
            os.makedirs(outdir, exist_ok=True)

        filepath = os.path.join(outdir, filename)
        return filepath

    def figure_path(self, measure, suffix):
        filename = "{}.{}.png".format(measure.measure_id, suffix)
        filepath = os.path.join(
            self.phenotype_data.pheno_id,
            measure.instrument_name,
            filename
        )
        return filepath

    def save_fig(self, measure, suffix):
        if "/" in measure.measure_id:
            return (None, None)

        small_filepath = self.figure_filepath(
            measure, "{}_small".format(suffix)
        )
        plt.savefig(small_filepath, dpi=self.SMALL_DPI)

        filepath = self.figure_filepath(measure, suffix)
        plt.savefig(filepath, dpi=self.LARGE_DPI)
        plt.close()
        return (
            self.figure_path(measure, "{}_small".format(suffix)),
            self.figure_path(measure, suffix),
        )

    def build_regression(self, dependent_measure, independent_measure, jitter):
        MIN_VALUES = 5
        MIN_UNIQUE_VALUES = 2

        res = {}

        if dependent_measure.measure_id == independent_measure.measure_id:
            return res

        aug_col_name = independent_measure.measure_name

        aug_df = self._augment_measure_values_df(
            independent_measure, aug_col_name, dependent_measure
        )

        if aug_df is None:
            return res

        aug_df = aug_df[aug_df.role == Role.prb]
        aug_df.loc[:, aug_col_name] = aug_df[aug_col_name].astype(np.float32)
        aug_df = aug_df[np.isfinite(aug_df[aug_col_name])]

        if (
            aug_df[dependent_measure.measure_id].nunique() < MIN_UNIQUE_VALUES
            or len(aug_df) <= MIN_VALUES
        ):
            return res

        res_male, res_female = draw_linregres(
            aug_df, aug_col_name, dependent_measure.measure_id, jitter
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
                dependent_measure, "prb_regression_by_{}".format(aug_col_name)
            )
        return res

    def build_values_violinplot(self, measure):
        df = self.load_measure(measure)
        drawn = draw_measure_violinplot(df, measure.measure_id)

        res = {}

        if drawn:
            (
                res["figure_distribution_small"],
                res["figure_distribution"],
            ) = self.save_fig(measure, "violinplot")

        return res

    def build_values_categorical_distribution(self, measure):
        df = self.load_measure(measure)
        drawn = draw_categorical_violin_distribution(df, measure.measure_id)

        res = {}
        if drawn:
            (
                res["figure_distribution_small"],
                res["figure_distribution"],
            ) = self.save_fig(measure, "distribution")

        return res

    def build_values_other_distribution(self, measure):
        df = self.load_measure(measure)
        drawn = draw_categorical_violin_distribution(df, measure.measure_id)

        res = {}
        if drawn:
            (
                res["figure_distribution_small"],
                res["figure_distribution"],
            ) = self.save_fig(measure, "distribution")

        return res

    def build_values_ordinal_distribution(self, measure):
        df = self.load_measure(measure)
        drawn = draw_ordinal_violin_distribution(df, measure.measure_id)

        res = {}
        if drawn:
            (
                res["figure_distribution_small"],
                res["figure_distribution"],
            ) = self.save_fig(measure, "distribution")

        return res

    def dump_browser_variable(self, var):
        print("-------------------------------------------")
        print(var["measure_id"])
        print("-------------------------------------------")
        print("instrument:  {}".format(var["instrument_name"]))
        print("measure:     {}".format(var["measure_name"]))
        print("type:        {}".format(var["measure_type"]))
        print("description: {}".format(var["description"]))
        print("domain:      {}".format(var["values_domain"]))
        print("-------------------------------------------")

    def _get_measure_by_name(self, measure_name, instrument_name):
        if instrument_name:
            measure_id = ".".join([instrument_name, measure_name])
            if self.phenotype_data.has_measure(measure_id):
                return self.phenotype_data.get_measure(measure_id)
        return None

    def handle_measure(self, measure):
        res = PreparePhenoBrowserBase._measure_to_dict(measure)

        if measure.measure_type == MeasureType.continuous:
            res.update(self.build_values_violinplot(measure))
        elif measure.measure_type == MeasureType.ordinal:
            res.update(self.build_values_ordinal_distribution(measure))
        elif measure.measure_type == MeasureType.categorical:
            res.update(self.build_values_categorical_distribution(measure))

        return res

    def _has_regression_measure(self, measure_name, instrument_name):
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

    def handle_regressions(self, measure):
        if measure.measure_type not in [
            MeasureType.continuous,
            MeasureType.ordinal,
        ]:
            return
        for reg_id, reg in self.pheno_regressions.regression.items():
            res = {"measure_id": measure.measure_id}
            reg_measure = self._get_measure_by_name(
                reg.measure_name,
                reg.instrument_name or measure.instrument_name,
            )
            if not reg_measure:
                continue
            if self._has_regression_measure(
                measure.measure_name, measure.instrument_name
            ):
                continue

            res["regression_id"] = reg_id
            res.update(self.build_regression(measure, reg_measure, reg.jitter))
            if (
                res.get("pvalue_regression_male") is not None
                or res.get("pvalue_regression_female") is not None
            ):
                yield res

    def run(self):
        pheno_dbfile = self.phenotype_data.db.pheno_dbfile
        db = DbManager(pheno_dbfile, browser_dbfile=self.browser_db)
        db.build()

        if self.pheno_regressions:
            for reg_id, reg_data in self.pheno_regressions.regression.items():
                db.save_regression(
                    {
                        "regression_id": reg_id,
                        "instrument_name": reg_data.instrument_name,
                        "measure_name": reg_data.measure_name,
                        "display_name": reg_data.display_name,
                    }
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
