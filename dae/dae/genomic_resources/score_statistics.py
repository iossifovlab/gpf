import os
import numpy as np
import logging
import yaml
import pandas as pd

from dae.genomic_resources.genomic_scores import open_score_from_resource

logger = logging.getLogger(__name__)


class Histogram:
    def __init__(
        self, bins_count,
        x_min, x_max, x_scale, y_scale,
        x_min_log=None
    ):
        self.x_min = x_min
        self.x_max = x_max
        self.x_scale = x_scale
        self.y_scale = y_scale
        self.x_min_log = x_min_log

        if self.x_scale == "linear":
            self.bins = np.linspace(
                self.x_min,
                self.x_max,
                bins_count + 1,
            )
        elif self.x_scale == "log":
            assert x_min_log is not None
            self.bins = np.array([
                self.x_min,
                * np.logspace(
                    np.log10(self.x_min_log),
                    np.log10(self.x_max),
                    bins_count
                )])
        else:
            assert False, f"unexpected xscale: {self.x_scale}"

        assert self.y_scale in ("linear", "log"), \
            f"unexpected yscale {self.y_scale}"

        self.y_scale = y_scale

        self.bars = np.zeros(bins_count, dtype=np.int32)

    @staticmethod
    def from_config(conf):
        return Histogram(
            conf["bins"],
            conf["min"],
            conf["max"],
            conf.get("x_scale", "linear"),
            conf.get("y_scale", "linear"),
            conf.get("x_min_log")
        )

    def to_dict(self):
        return {
            "bins_count": len(self.bins),
            "bins": self.bins.tolist(),
            "bars": self.bars.tolist(),
            "x_min": self.x_min,
            "x_max": self.x_max,
            "x_scale": self.x_scale,
            "y_scale": self.y_scale,
        }

    @staticmethod
    def from_dict(d):
        hist = Histogram(
            d["bins_count"], d["x_min"], d["x_max"],
            d["x_scale"], d["y_scale"]
        )

        hist.bins = np.array(d["bins"])
        hist.bars = np.array(d["bars"], dtype=np.int32)

        return hist

    @staticmethod
    def merge(hist1, hist2):
        assert hist1.x_scale == hist2.x_scale
        assert hist1.x_min == hist2.x_min
        assert hist1.x_min_log == hist2.x_min_log
        assert hist1.x_max == hist2.x_max
        assert all(hist1.bins == hist2.bins)

        result = Histogram(
            len(hist1.bins),
            hist1.x_min,
            hist1.x_max,
            hist1.x_scale,
            hist1.y_scale,
            hist1.x_min_log
        )

        result.bins = hist1.bins

        result.bars += hist1.bars
        result.bars += hist2.bars

        return result

    def add_value(self, value):
        if value < self.x_min or value > self.x_max:
            logger.warning(
                f"value {value} out of range: [{self.x_min},{self.x_max}]")
            return False
        index = np.where(self.bins > value)
        if len(index) == 0:
            logger.warning(f"(1) empty index {index} for value {value}")
            return False
        index = index[0]
        if len(index) == 0:
            logger.info(f"(2) empty index {index} for value {value}")
            self.bars[-1] += 1
            return True

        if index[0] == 0:
            logger.warning(
                f"value: {value}; with index {index} in bins: {self.bins}")

        self.bars[index[0] - 1] += 1

        return True


class HistogramBuilder:
    def build(self, resource) -> dict[str, Histogram]:
        histogram_desc = resource.get_config().get("histograms", [])
        if len(histogram_desc) == 0:
            return {}
        histograms = {hist["score"]: Histogram.from_config(hist)
                      for hist in histogram_desc}
        score_names = list(histograms.keys())
        score = open_score_from_resource(resource)

        chromosomes = score.get_all_chromosomes()
        for chrom in chromosomes:
            score_to_values = \
                score.fetch_region(chrom, None, None, score_names)
            for scr_id, vals_iter in score_to_values.items():
                hist = histograms[scr_id]
                for v in vals_iter:
                    if v is not None:  # None designates missing values
                        hist.add_value(v)

        return histograms

    # def build():
    #     over all chromosomes:
    #         run build_region in parallel
    #     merge all histograms.

    def save(self, histograms, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        for score, histogram in histograms.items():
            df = pd.DataFrame({'bars': histogram.bars,
                               'bins': histogram.bins[:-1]})
            hist_name = f"{score}.csv"
            df.to_csv(os.path.join(out_dir, hist_name), index=None)


class ScoreStatistic:
    def to_dict(self):
        raise NotImplementedError()

    @classmethod
    def from_dict(cls, d):
        raise NotImplementedError()

    @classmethod
    def from_yaml(cls, filepath):
        with open(filepath, "r") as file:
            try:
                content = yaml.safe_load(file)
                return cls.from_dict(content)
            except yaml.YAMLError as exc:
                logger.error(exc)
                return None


class PositionScoreStatistic(ScoreStatistic):
    def __init__(self, histogram):
        self.min_value = None
        self.max_value = None
        self.histogram = histogram
        self.positions_covered = dict()
        self.positions_covered_all = None
        self.missing_count = None

    def to_dict(self):
        return {
            "min_value": self.min_value,
            "max_value": self.max_value,
            "histogram": self.histogram.to_dict(),
            "positions_covered": self.positions_covered,
            "positions_covered_all": self.positions_covered_all,
            "missing_count": self.missing_count
        }

    @classmethod
    def from_dict(cls, d):
        return PositionScoreStatistic(
            d["min_value"], d["max_value"],
            Histogram.from_dict(d["histogram"]),
            d["positions_covered"], d["positions_covered_all"],
            d["missing_count"]
        )


class NPScoreStatistic(ScoreStatistic):
    pass


class AlleleScoreStatistic(ScoreStatistic):
    pass
