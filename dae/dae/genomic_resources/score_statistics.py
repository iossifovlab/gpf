import logging
import yaml

logger = logging.getLogger(__name__)


class Histogram:
    def __init__(self, bins, bars, x_max, x_scale, y_max, y_scale):
        self.bins = bins
        self.bars = bars
        self.x_max = x_max
        self.x_scale = x_scale
        self.y_max = y_max
        self.y_scale = y_scale

    @staticmethod
    def from_config(conf):
        return Histogram(
            conf["bins"],
            conf["bars"],
            conf["x_max"],
            conf["x_scale"],
            conf["y_max"],
            conf["y_scale"]
        )


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
            d["min_value"], d["max_value"], d["histogram"],
            d["positions_covered"], d["positions_covered_all"],
            d["missing_count"]
        )


class NPScoreStatistic(ScoreStatistic):
    pass


class AlleleScoreStatistic(ScoreStatistic):
    pass
