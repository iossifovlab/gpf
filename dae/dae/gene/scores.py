import os
import pandas as pd
import logging

from dae.file_cache.cache import ResourceFileCache


logger = logging.getLogger(__name__)


class GenomicScore:
    def __init__(self, resource, score_id, file_cache):

        self.resource = resource
        self.config = resource.get_config()
        self.genomic_values_col = "scores"

        self.id = score_id
        self.df = None
        self.file_cache = file_cache

        for score_conf in self.config["scores"]:
            if score_conf["id"] == score_id:
                self.score_config = score_conf
        for hist_conf in self.config["histograms"]:
            if hist_conf["score"] == score_id:
                self.histogram_config = hist_conf

        self.desc = self.score_config["desc"]
        self.bins = self.histogram_config["bins"]
        self.xscale = self.histogram_config.get("xscale", "linear")
        self.yscale = self.histogram_config.get("yscale", "linear")
        self.filename = os.path.join("histograms", score_id)
        self.help_filename = os.path.join("histograms", f"{score_id}.md")
        self.range = None
        help_filepath = self.file_cache.get_file_path_from_resource(
            self.resource, self.help_filename
        )
        if help_filepath is not None:
            with open(help_filepath, "r") as infile:
                self.help = infile.read()
        else:
            self.help = None

        self._load_data()
        self.df.fillna(value=0, inplace=True)

    def _load_data(self):
        assert self.filename is not None
        filepath = self.file_cache.get_file_path_from_resource(
            self.resource, self.filename
        )

        df = pd.read_csv(filepath)
        assert self.id in df.columns, "{} not found in {}".format(
            self.id, df.columns
        )
        self.df = df[[self.genomic_values_col, self.id]].copy()
        return self.df

    def values(self):
        return self.df[self.id].values

    def get_scores(self):
        return self.df[self.genomic_values_col].values


class GenomicScoresDB:
    def __init__(self, grr, scores, cache_dir=None):
        self.grr = grr
        if cache_dir is None:
            dae_db_dir = os.environ.get("DAE_DB_DIR")
            cache_dir = os.path.join(
                dae_db_dir, "file_cache", "genomic_scores_db"
            )
        self.file_cache = ResourceFileCache(cache_dir, grr)

        self.scores = {}
        for resource_id, score_id in scores:
            resource = self.grr.get_resource(resource_id)
            try:
                score = GenomicScore(
                    resource, score_id, self.file_cache
                )
                self.scores[score_id] = score
            except KeyError:
                logger.warn(
                    f"Failed to load histogram configuration of {resource_id}"
                )

    def get_scores(self):
        result = []

        for score in self.scores.values():
            assert score.df is not None
            result.append(score)

        return result

    def __getitem__(self, score_id):
        if score_id not in self.scores:
            raise KeyError()

        res = self.scores[score_id]
        if res.df is None:
            res.load_scores()
        return res

    def __contains__(self, score_id):
        return score_id in self.scores
