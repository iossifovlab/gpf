import hashlib
import os
import numpy as np
import logging
import yaml
import pandas as pd
from typing import Dict
from copy import copy
import matplotlib.pyplot as plt

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

        self.bars = np.zeros(bins_count, dtype=np.int64)

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
        hist.bars = np.array(d["bars"], dtype=np.int64)

        return hist

    @staticmethod
    def merge(hist1, hist2):
        assert hist1.x_scale == hist2.x_scale
        assert hist1.x_min == hist2.x_min
        assert hist1.x_min_log == hist2.x_min_log
        assert hist1.x_max == hist2.x_max
        assert all(hist1.bins == hist2.bins)

        result = Histogram(
            len(hist1.bins) - 1,
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
    def __init__(self, resource) -> None:
        self.resource = resource

    def build(self, client, path="histograms",
              force=False, only_dirty=False) -> dict[str, Histogram]:
        loaded_hists, computed_hists = self._build(client, path, force)
        if only_dirty:
            return computed_hists
        else:
            for k, v in computed_hists.items():
                loaded_hists[k] = v
            return loaded_hists

    def _build(self, client, path, force) -> dict[str, Histogram]:
        histogram_desc = self.resource.get_config().get("histograms", [])
        if force:
            return {}, self._do_build(client, histogram_desc)

        hists, metadata = _load_histograms(self.resource.repo,
                                           self.resource.get_id(), None, None,
                                           path)
        hashes = self._build_hashes()

        configs_to_calculate = []
        loaded_hists = {}
        for hist_conf in histogram_desc:
            score_id = hist_conf["score"]
            actual_md5 = metadata.get(score_id, {}).get("md5", None)
            expected_md5 = hashes.get(score_id, None)
            if actual_md5 == expected_md5:
                logger.info(f"Skipping calculation of score "
                            f"{hist_conf['score']} as it's already calculated"
                            )
                loaded_hists[score_id] = hists[score_id]
            else:
                configs_to_calculate.append(hist_conf)

        remaining = self._do_build(client, configs_to_calculate)

        return loaded_hists, remaining

    def _do_build(self, client, histogram_desc) -> dict[str, Histogram]:
        if len(histogram_desc) == 0:
            return {}

        scores_missing_limits = []
        for hist_conf in histogram_desc:
            has_min_max = "min" in hist_conf and "max" in hist_conf
            if not has_min_max:
                scores_missing_limits.append(hist_conf["score"])

        score = open_score_from_resource(self.resource)
        score_limits = {}
        if len(scores_missing_limits) > 0:
            # copy hist desc so that we don't overwrite the config
            histogram_desc = [copy(d) for d in histogram_desc]
            score_limits = self._score_min_max(client, score,
                                               scores_missing_limits)

        hist_configs = {}
        for hist_conf in histogram_desc:
            if "min" not in hist_conf:
                hist_conf["min"] = score_limits[hist_conf["score"]][0]
            if "max" not in hist_conf:
                hist_conf["max"] = score_limits[hist_conf["score"]][1]
            hist_configs[hist_conf["score"]] = hist_conf

        chrom_histograms = []
        futures = []
        chromosomes = score.get_all_chromosomes()
        for chrom in chromosomes:
            futures.append(client.submit(self._do_hist,
                                         chrom, hist_configs))
        for future in futures:
            chrom_histograms.append(future.result())

        return self._merge_histograms(chrom_histograms)

    def _do_hist(self, chrom, hist_configs):
        histograms = {}
        for scr_id, config in hist_configs.items():
            histograms[scr_id] = Histogram.from_config(config)
        score_names = list(histograms.keys())

        score = open_score_from_resource(self.resource)
        for rec in score.fetch_region(chrom, None, None, score_names):
            for scr_id, v in rec.items():
                hist = histograms[scr_id]
                if v is not None:  # None designates missing values
                    hist.add_value(v)

        return histograms

    @staticmethod
    def _merge_histograms(chrom_histograms) -> Dict[str, Histogram]:
        res = {}
        for histograms in chrom_histograms:
            for scr_id, histogram in histograms.items():
                if scr_id not in res:
                    res[scr_id] = histogram
                else:
                    res[scr_id] = Histogram.merge(res[scr_id], histogram)
        return res

    def _score_min_max(self, client, score, score_ids):
        logger.info(f"Calculating min max for {score_ids}")

        chromosomes = score.get_all_chromosomes()
        min_maxes = []
        futures = []
        for chrom in chromosomes:
            futures.append(client.submit(self._min_max_for_chrom,
                                         chrom, score_ids))
        for future in futures:
            min_maxes.append(future.result())

        res = {}
        for partial_res in min_maxes:
            for scr_id, (i_min, i_max) in partial_res.items():
                if scr_id in res:
                    res[scr_id][0] = min(i_min, res[scr_id][0])
                    res[scr_id][1] = max(i_max, res[scr_id][1])
                else:
                    res[scr_id] = [i_min, i_max]

        logger.info(f"Done calculating min/max for {score_ids}.\
 res={res}")
        return res

    def _min_max_for_chrom(self, chrom, score_ids):
        score = open_score_from_resource(self.resource)
        limits = np.iinfo(np.int64)
        res = {scr_id: [limits.max, limits.min] for scr_id in score_ids}
        for rec in score.fetch_region(chrom, None, None, score_ids):
            for scr_id in score_ids:
                v = rec[scr_id]
                if v is not None:  # None designates missing values
                    res[scr_id][0] = min(v, res[scr_id][0])
                    res[scr_id][1] = max(v, res[scr_id][1])
        return res

    def _build_hashes(self):
        config = self.resource.get_config()
        table_filename = config["table"]["filename"]
        manifest = self.resource.get_manifest()
        table_hash = None
        for rec in manifest:
            if rec["name"] == table_filename:
                table_hash = rec["md5"]
                break
        if table_hash is None:
            return {}

        histogram_desc = config.get("histograms", [])
        hist_configs = {hist['score']: hist for hist in histogram_desc}
        hashes = {}
        for score_id, hist_config in hist_configs.items():
            md5_hash = hashlib.md5()
            hist_hash_obj = {"table_hash": table_hash, "config": hist_config}
            md5_hash.update(yaml.dump(hist_hash_obj).encode("utf-8"))
            hashes[score_id] = md5_hash.hexdigest()

        return hashes

    def save(self, histograms, out_dir):
        histogram_desc = self.resource.get_config().get("histograms", [])
        configs = {hist['score']: hist for hist in histogram_desc}
        hist_hashes = self._build_hashes()

        for score, histogram in histograms.items():
            df = pd.DataFrame({'bars': histogram.bars,
                               'bins': histogram.bins[:-1]})
            hist_file = os.path.join(out_dir, f"{score}.csv")
            with self.resource.open_raw_file(hist_file, "wt") as f:
                df.to_csv(f, index=None)

            hist_config = configs.get(score, {})
            metadata = {
                'resource': self.resource.get_id(),
                'histogram_config': hist_config,
            }
            if score in hist_hashes:
                metadata['md5'] = hist_hashes[score]
            if 'min' not in hist_config:
                metadata['calculated_min'] = histogram.x_min
            if 'max' not in hist_config:
                metadata['calculated_max'] = histogram.x_max
            metadata_file = os.path.join(out_dir, f"{score}.metadata.yaml")
            with self.resource.open_raw_file(metadata_file, "wt") as f:
                yaml.dump(metadata, f)

            plt.hist(histogram.bins[:-1], histogram.bins,
                     weights=histogram.bars, log=histogram.y_scale == "log")
            if histogram.x_scale == "log":
                plt.xscale("log")
            plt.grid(axis='y')
            plt.grid(axis='x')
            plot_file = os.path.join(out_dir, f"{score}.png")
            with self.resource.open_raw_file(plot_file, "wb") as f:
                plt.savefig(f)

        # update manifest with newly written files
        self.resource.update_manifest()


def load_histograms(repo, resource_id, version_constraint=None,
                    genomic_repository_id=None, path="histograms"):
    hists, _ = _load_histograms(repo, resource_id, version_constraint,
                                genomic_repository_id, path)
    return hists


def _load_histograms(repo, resource_id, version_constraint,
                     genomic_repository_id, path):
    from dae.genomic_resources.cached_repository import \
        GenomicResourceCachedRepo
    if isinstance(repo, GenomicResourceCachedRepo):
        # score resources are huge so circumvent the caching
        repo = repo.child

    res = repo.get_resource(resource_id, version_constraint,
                            genomic_repository_id)
    hists = {}
    metadatas = {}
    for hist_config in res.get_config().get('histograms', []):
        score = hist_config['score']
        hist_file = os.path.join(path, f"{score}.csv")
        metadata_file = os.path.join(path, f"{score}.metadata.yaml")
        if res.file_exists(hist_file) and res.file_exists(metadata_file):
            with res.open_raw_file(hist_file, "rt") as f:
                df = pd.read_csv(f)
            with res.open_raw_file(metadata_file, "rt") as f:
                metadata = yaml.safe_load(f)
            hist_config = metadata['histogram_config']
            if 'min' not in hist_config:
                hist_config['min'] = metadata['calculated_min']
            if 'max' not in hist_config:
                hist_config['max'] = metadata['calculated_max']
            hist = Histogram.from_config(hist_config)
            hist.bars = df["bars"].to_numpy()
            hists[score] = hist
            metadatas[score] = metadata
    return hists, metadatas


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
