"""Handling of genomic scores statistics.

Currently we support only genomic scores histograms.
"""
from __future__ import annotations

import hashlib
import os
import logging
from typing import Dict, Any, cast
from copy import copy, deepcopy

import yaml
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt  # type: ignore
from tqdm import tqdm  # type: ignore
from dask.distributed import as_completed  # type: ignore

from dae.genomic_resources.genomic_scores import build_score_from_resource
from dae.genomic_resources.statistic import Statistic

logger = logging.getLogger(__name__)


class Histogram(Statistic):
    """Class to represent a histogram."""

    # pylint: disable=too-many-instance-attributes
    # FIXME:
    def __init__(self, config, bins=None, bars=None):
        super().__init__("histogram", "Collects values for histogram.")
        self.config = config
        self.bins = bins
        self.bars = bars

        try:
            self.bins_count = self.config["bins"]
            self.x_min = self.config["x_min"]
            self.x_max = self.config["x_max"]
            self.x_scale = self.config["x_scale"]
            self.y_scale = self.config["y_scale"]
        except KeyError as e:
            raise ValueError(
                f"Invalid histogram configuration, cannot find {e.args[0]}"
            ) from e

        self.x_min_log = self.config.get("x_min_log")

        if self.bins is None and self.bars is None:
            if self.x_scale == "linear":
                self.bins = np.linspace(
                    self.x_min,
                    self.x_max,
                    self.bins_count + 1,
                )
            elif self.x_scale == "log":
                assert self.x_min_log is not None
                self.bins = np.array([
                    self.x_min,
                    * np.logspace(
                        np.log10(self.x_min_log),
                        np.log10(self.x_max),
                        self.bins_count
                    )])
            self.bars = np.zeros(self.bins_count, dtype=np.int64)
        elif self.bins is None or self.bars is None:
            raise ValueError(
                f"Cannot instantiate histogram with only bins or only bars!"
            )

        if self.x_scale not in ("linear", "log"):
            raise ValueError(f"unexpected histogram xscale: {self.x_scale}")

        if self.y_scale not in ("linear", "log"):
            raise ValueError(f"unexpected yscale {self.y_scale}")

    def merge(self, other: Histogram) -> None:
        """Merge two histograms."""
        assert self.x_scale == other.x_scale
        assert self.x_min == other.x_min
        assert self.x_min_log == other.x_min_log
        assert self.x_max == other.x_max
        assert all(self.bins == other.bins)

        self.bars += other.bars

    @property
    def range(self):
        if self.x_min is not None and self.x_max is not None:
            return [self.x_min, self.x_max]
        return None

    def add_value(self, value):
        """Add value to the histogram."""
        if value < self.x_min:
            logger.warning(
                "value %s out of range: [%s, %s]; adding to the first bin",
                value, self.x_min, self.x_max)
            self.bars[0] += 1
            return False
        if value > self.x_max:
            logger.warning(
                "value %s out of range: [%s, %s]; adding to the last bin",
                value, self.x_min, self.x_max)
            self.bars[-1] += 1
            return False

        index = self.bins.searchsorted(value, side="right")
        if index == 0:
            logger.warning(
                "(1) empty index %s for value %s",
                index, value)
            return False
        if value == self.bins[-1]:
            self.bars[-1] += 1
            return True

        self.bars[index - 1] += 1
        return True

    def serialize(self) -> str:
        return cast(str, yaml.dump(
            {
                "config": self.config,
                "bins": self.bins,
                "bars": self.bars
            }
        ))

    @staticmethod
    def deserialize(data) -> Histogram:
        res = yaml.load(data, yaml.Loader)
        return Histogram(
            res.get("config"),
            bins=res.get("bins"),
            bars=res.get("bars")
        )


class HistogramBuilder:
    """Class to build genomic scores histograms for given resource."""

    def __init__(self, resource) -> None:
        self.resource = resource

    def build(self, client,
              region_size=1_000_000, **_kwargs) -> dict[str, Histogram]:
        """Build a genomic score's histograms and returns them."""
        return self._do_build(
            client,
            self.resource.get_config().get("histograms", []),
            region_size)

    def _collect_histograms_to_build(self, path):
        hist_configs = self.resource.get_config().get("histograms", [])

        hists, metadata = _load_histograms(
            self.resource.proto,
            resource_id=self.resource.get_id(),
            version_constraint=f"={self.resource.get_version_str()}",
            path=path)
        hashes = self._build_hashes()

        configs_to_calculate = []
        loaded_hists = {}
        for hist_conf in hist_configs:
            score_id = hist_conf["score"]
            actual_md5 = metadata.get(score_id, {}).get("md5", None)
            expected_md5 = hashes.get(score_id, None)
            if actual_md5 == expected_md5:
                logger.debug(
                    "Skipping calculation of score "
                    "%s as it's already calculated",
                    hist_conf["score"])
                loaded_hists[score_id] = hists[score_id]
            else:
                configs_to_calculate.append(hist_conf)
        return loaded_hists, configs_to_calculate

    def check_update(self, path="histograms"):
        """Check if histograms of a given reource need update."""
        _, configs_to_calculate = \
            self._collect_histograms_to_build(path)
        if configs_to_calculate:
            logger.info(
                "resource <%s> histograms %s need update",
                self.resource.get_genomic_resource_id_version(),
                configs_to_calculate)
        else:
            logger.info(
                "histograms of <%s> are up to date",
                self.resource.get_genomic_resource_id_version())
        return configs_to_calculate

    def update(
            self, client, path="histograms",
            region_size=1_000_000) -> Dict[str, Histogram]:
        """Build a genomic score's histograms that need rebuilding."""
        configs_to_calculate = self.check_update(path=path)
        return self._do_build(client, configs_to_calculate, region_size)

    def _do_fill_min_maxes(
            self, client, score, hist_configs, region_size):
        hist_configs = deepcopy(hist_configs)

        scores_missing_limits = []
        for hist_conf in hist_configs:
            has_min_max = "min" in hist_conf and "max" in hist_conf
            if not has_min_max:
                scores_missing_limits.append(hist_conf["score"])

        score_limits = {}
        if len(scores_missing_limits) > 0:
            # copy hist desc so that we don't overwrite the config
            score_limits = self._score_min_max(client, score,
                                               scores_missing_limits,
                                               region_size)

        result = {}
        for hist_conf in hist_configs:
            if "min" not in hist_conf:
                hist_conf["min"] = score_limits[hist_conf["score"]][0]
            if "max" not in hist_conf:
                hist_conf["max"] = score_limits[hist_conf["score"]][1]
            result[hist_conf["score"]] = hist_conf

        return result

    def _do_build(self, client, histogram_desc,
                  region_size) -> dict[str, Histogram]:
        if len(histogram_desc) == 0:
            return {}

        score = build_score_from_resource(self.resource).open()

        hist_configs = self._do_fill_min_maxes(
            client, score, histogram_desc, region_size)

        chrom_histograms = []
        futures = []
        for chrom, start, end in self._split_into_regions(score, region_size):
            futures.append(client.submit(
                self._do_hist,
                chrom, hist_configs,
                start, end))
        for future in tqdm(as_completed(futures), total=len(futures)):
            chrom_histograms.append(future.result())

        return self._merge_histograms(chrom_histograms)

    @staticmethod
    def _split_into_regions(score, region_size):
        chromosomes = score.get_all_chromosomes()
        for chrom in chromosomes:
            chrom_len = score.table.get_chromosome_length(chrom)
            logger.debug(
                "Chromosome '%s' has length %s",
                chrom, chrom_len)
            i = 1
            while i < chrom_len - region_size:
                yield chrom, i, i + region_size - 1
                i += region_size
            yield chrom, i, None

    def _do_hist(self, chrom, hist_configs, start, end):
        histograms = {}
        for scr_id, config in hist_configs.items():
            hist = Histogram.from_config(config)
            histograms[scr_id] = hist
            hist.set_empty()

        score_names = list(histograms.keys())

        score = build_score_from_resource(self.resource).open()

        for rec in score.fetch_region(chrom, start, end, score_names):
            for scr_id, value in rec.items():
                hist = histograms[scr_id]

                if value is not None:  # None designates missing values
                    hist.add_value(value)

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

    @staticmethod
    def _merge_min_maxes(min_maxes):
        res = {}
        for partial_res in min_maxes:
            for scr_id, (i_min, i_max) in partial_res.items():
                if scr_id in res:
                    res[scr_id][0] = min(i_min, res[scr_id][0])
                    res[scr_id][1] = max(i_max, res[scr_id][1])
                else:
                    res[scr_id] = [i_min, i_max]
        return res

    def _score_min_max(self, client, score, score_ids, region_size):
        logger.info("Calculating min max for %s", score_ids)

        min_maxes = []
        futures = []
        for chrom, start, end in self._split_into_regions(score, region_size):
            futures.append(client.submit(self._min_max_for_region,
                                         chrom, score_ids,
                                         start, end))
        for future in tqdm(as_completed(futures), total=len(futures)):
            min_maxes.append(future.result())

        res = self._merge_min_maxes(min_maxes)
        logger.info(
            "Done calculating min/max for %s. "
            "res=%s", score_ids, res)
        return res

    def _min_max_for_region(self, chrom, score_ids, start, end):
        score = build_score_from_resource(self.resource).open()

        limits = np.iinfo(np.int64)
        res = {scr_id: [limits.max, limits.min] for scr_id in score_ids}
        for rec in score.fetch_region(chrom, start, end, score_ids):
            for scr_id in score_ids:
                val = rec[scr_id]
                if val is not None:  # None designates missing values
                    res[scr_id][0] = min(val, res[scr_id][0])
                    res[scr_id][1] = max(val, res[scr_id][1])
        return res

    def _get_table_hash(self):
        config = self.resource.get_config()
        if config.get("table") is None:
            return None

        table_filename = config["table"]["filename"]
        index_filename = f"{table_filename}.tbi"

        manifest = self.resource.get_manifest()
        table_hash = None
        index_hash = ""
        for rec in manifest:
            if rec.name == table_filename:
                table_hash = rec.md5
            elif rec.name == index_filename:
                index_hash = rec.md5
        if table_hash is None:
            raise ValueError(f"cant get table md5 hash for {table_filename}")

        return (table_hash, index_hash)

    def _build_hashes(self):
        config = self.resource.get_config()
        histogram_desc = config.get("histograms", [])
        if not histogram_desc:
            return {}

        hist_configs = {hist["score"]: copy(hist) for hist in histogram_desc}
        table_hash = self._get_table_hash()
        if table_hash is None:
            return {}

        for hist_score, hist_conf in hist_configs.items():
            for score_desc in config["scores"]:
                if hist_score == score_desc["id"]:
                    hist_conf["score_desc"] = score_desc

        hashes = {}
        for score_id, hist_config in hist_configs.items():
            md5_hash = hashlib.md5()
            hist_hash_obj = {
                "table_hash": table_hash[0],
                "index_hash": table_hash[1],
                "config": hist_config
            }
            md5_hash.update(yaml.dump(hist_hash_obj).encode("utf-8"))
            hashes[score_id] = md5_hash.hexdigest()

        return hashes

    def _save_plt(self, histogram, score, out_dir):
        width = histogram.bins[1:] - histogram.bins[:-1]
        plt.bar(
            x=histogram.bins[:-1], height=histogram.bars,
            log=histogram.y_scale == "log",
            width=width,
            align="edge")

        if histogram.x_scale == "log":
            plt.xscale("log")
        plt.grid(axis="y")
        plt.grid(axis="x")
        plot_file = os.path.join(out_dir, f"{score}.png")
        with self.resource.open_raw_file(plot_file, "wb") as outfile:
            plt.savefig(outfile)
        plt.clf()

    def save(self, histograms, out_dir):
        """Save a histogram in the specified output directory."""
        histogram_desc = self.resource.get_config().get("histograms", [])
        configs = {hist["score"]: hist for hist in histogram_desc}
        hist_hashes = self._build_hashes()

        for score, histogram in histograms.items():
            bars = list(histogram.bars)
            bars.append(np.nan)

            data = pd.DataFrame({
                "bars": bars,
                "bins": histogram.bins
            })
            hist_file = os.path.join(out_dir, f"{score}.csv")
            with self.resource.open_raw_file(hist_file, "wt") as outfile:
                data.to_csv(outfile, index=None)

            hist_config = configs.get(score, {})
            metadata = {
                "resource": self.resource.get_id(),
                "histogram_config": hist_config,
            }
            if score in hist_hashes:
                metadata["md5"] = hist_hashes[score]
            if "min" not in hist_config:
                metadata["calculated_min"] = histogram.x_min
            if "max" not in hist_config:
                metadata["calculated_max"] = histogram.x_max
            metadata_file = os.path.join(out_dir, f"{score}.metadata.yaml")
            with self.resource.open_raw_file(metadata_file, "wt") as outfile:
                yaml.dump(metadata, outfile)
            self._save_plt(histogram, score, out_dir)


def load_histograms(repo, resource_id, version_constraint=None,
                    repository_id=None, path="histograms"):
    """Load genomic score histograms."""
    if repository_id is not None and repository_id != repo.get_id():
        return {}

    hists, _ = _load_histograms(repo, resource_id, version_constraint, path)
    return hists


def _load_histograms(repo, resource_id, version_constraint, path):

    res = repo.get_resource(resource_id, version_constraint)
    hists = {}
    metadatas = {}
    for hist_config in res.get_config().get("histograms", []):
        score = hist_config["score"]
        hist_file = os.path.join(path, f"{score}.csv")
        metadata_file = os.path.join(path, f"{score}.metadata.yaml")

        if res.file_exists(hist_file) and res.file_exists(metadata_file):
            with res.open_raw_file(hist_file, "rt") as infile:
                data = pd.read_csv(infile)
            with res.open_raw_file(metadata_file, "rt") as infile:
                metadata = yaml.safe_load(infile)
            hist_config = metadata["histogram_config"]
            if "min" not in hist_config:
                hist_config["min"] = metadata["calculated_min"]
            if "max" not in hist_config:
                hist_config["max"] = metadata["calculated_max"]
            hist = Histogram.from_config(hist_config)
            hist.bars = data["bars"].to_numpy()[:-1]
            hist.bins = data["bins"].to_numpy()

            hists[score] = hist
            metadatas[score] = metadata
    return hists, metadatas
