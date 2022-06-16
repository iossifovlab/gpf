import os
import logging
import pandas as pd

from dae.genomic_resources.histogram import Histogram


logger = logging.getLogger(__name__)


class GenomicScoresDb:
    """Genomic scores DB allowing access to genomic scores histograms"""
    def __init__(self, grr, scores, cache_dir=None):
        self.grr = grr

        self.scores = {}
        for resource_id, selected_score_id in scores:
            resource = self.grr.get_resource(resource_id)
            if resource is None:
                logger.error(
                    "unable to find resource %s in GRR", resource_id)
                continue
            conf = resource.get_config()
            for histogram_config in conf["histograms"]:
                try:
                    score = Histogram.from_config(
                        histogram_config
                    )
                    score_id = histogram_config["score"]
                    if score_id != selected_score_id:
                        continue
                    resource_file = os.path.join(
                        "histograms", f"{score_id}.csv"
                    )
                    with resource.open_raw_file(resource_file) as infile:
                        df = pd.read_csv(infile, na_filter=False)
                    assert set(df.columns) == set(["bars", "bins"]), \
                        "Incorrect CSV file"
                    bins = df["bins"].values
                    bars = df["bars"].values
                    score.bins = bins
                    score.bars = bars

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

        for score_id, score in self.scores.items():
            result.append((score_id, score))

        return result

    def __getitem__(self, score_id):
        if score_id not in self.scores:
            raise KeyError()

        res = self.scores[score_id]
        return res

    def __contains__(self, score_id):
        return score_id in self.scores
