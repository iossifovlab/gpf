import os
import logging
import pandas as pd

from dae.file_cache.cache import ResourceFileCache


logger = logging.getLogger(__name__)


class GenomicScore:
    """Genomic scores histograms"""
    def __init__(self, resource, score_id, file_cache):

        self.resource = resource
        self.config = resource.get_config()

        self.id = score_id
        self.df = None
        self.file_cache = file_cache

        self.source = None
        annotation_conf = self.config["default_annotation"]
        for attr in annotation_conf["attributes"]:
            if attr["destination"] == self.id:
                self.source = attr["source"]
        assert self.source is not None, f"{score_id} source not found"
        for score_conf in self.config["scores"]:
            if score_conf["id"] == self.source:
                self.score_config = score_conf
        for hist_conf in self.config["histograms"]:
            if hist_conf["score"] == self.source:
                self.histogram_config = hist_conf

        self.desc = self.score_config["desc"]
        self.bins_count = self.histogram_config["bins"]
        self.min = self.histogram_config.get("min", None)
        self.max = self.histogram_config.get("max", None)
        self.xscale = self.histogram_config.get("x_scale", "linear")
        self.yscale = self.histogram_config.get("y_scale", "linear")
        self.filename = os.path.join("histograms", f"{self.source}.csv")
        self.help = self.config.get("meta", None)
        self.range = None

        self._load_data()
        self.df.fillna(value=0, inplace=True)

    def _load_data(self):
        assert self.filename is not None
        filepath = self.file_cache.get_file_path_from_resource(
            self.resource, self.filename
        )
        assert filepath is not None, \
            f"Couldn't find csv {self.filename} in {self.resource.resource_id}"

        df = pd.read_csv(filepath)
        assert set(df.columns) == set(["bars", "bins"]), "Incorrect CSV file"
        self.df = df
        return self.df

    @property
    def bars(self):
        return self.df["bars"].values

    @property
    def bins(self):
        return self.df["bins"].values


class GenomicScoresDB:
    """Genomic scores DB allowing access to gnomic scores histograms"""
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
            if resource is None:
                logger.error(
                    "unable to find resource %s in GRR", resource_id)
                continue
            try:
                score = GenomicScore(
                    resource, score_id, self.file_cache
                )
                self.scores[score_id] = score
            except KeyError as err:
                logger.error(
                    "Failed to load histogram of %s; "
                    "Couldn't find key %s", resource_id, err)
            except AssertionError as err:
                logger.error(
                    "Incorrect configuration of %s; "
                    "histogram resource: %s", resource_id, err)

    def get_scores(self):
        "Returns all genomic scores histograms"
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
