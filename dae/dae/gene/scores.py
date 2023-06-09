import logging
from dataclasses import dataclass

from dae.genomic_resources.genomic_scores import build_score_from_resource
from dae.genomic_resources.histogram import NumberHistogram, \
    NumberHistogramConfig


logger = logging.getLogger(__name__)


@dataclass
class ScoreDesc:
    resource_id: str
    score_id: str
    source: str
    destination: str
    hist: NumberHistogram
    description: str


class GenomicScoresDb:
    """Genomic scores DB allowing access to genomic scores histograms."""

    def __init__(self, grr, score_annotators):
        self.grr = grr
        self.scores = {}
        for annotator_info in score_annotators:
            assert len(annotator_info.resources) == 1, annotator_info
            resource = annotator_info.resources[0]
            if resource.get_type() not in {
                    "position_score", "np_score", "allele_score"}:
                logger.warning(
                    "wrong resource type passed to genomic scores: %s",
                    resource.resource_id)
                continue
            scores_desc = self._build_annotator_scores_desc(annotator_info)
            self.scores.update(scores_desc)
        logger.info(
            "genomic scores histograms loaded: %s", list(self.scores.keys()))

    @staticmethod
    def _build_annotator_scores_desc(annotator_info):
        resource = annotator_info.resources[0]
        score = build_score_from_resource(resource)
        result = {}
        for attr in annotator_info.attributes:
            if attr.internal:
                continue
            result[attr.name] = ScoreDesc(
                resource.resource_id,
                attr.source, attr.source,
                attr.name,
                None,  # score.get_score_config(attr.source).histogram,
                score.get_score_config(attr.source).desc)
        return result

    # @staticmethod
    # def _build_scores_desc(annotator_info):
    #     resource = annotator_info.resources[0]
    #     score = build_score_from_resource(resource)
    #     default_annotation = score.get_default_annotation()
    #     attributes_mapping = {
    #         attr.get("destination")
    #         if attr.get("destination") else attr["source"]: attr["source"]
    #         for attr in default_annotation.get("attributes", [])
    #     }
    #     logger.debug("default annotation: %s", default_annotation)
    #     if selected_score_id not in attributes_mapping:
    #         logger.warning(
    #             "unable to find %s in default annotation", selected_score_id)
    #         return None
    #     source_score_id = attributes_mapping[selected_score_id]
    #     conf = resource.get_config()
    #     description = selected_score_id
    #     for score_conf in conf["scores"]:
    #         if score_conf["id"] == source_score_id:
    #             description = score_conf.get(
    #                 "description", selected_score_id)
    #     for histogram_config in conf["histograms"]:
    #         try:
    #             hist = NumberHistogram(
    #                 NumberHistogramConfig.convert_legacy_config(
    #                     histogram_config
    #                 )
    #             )
    #             score_id = histogram_config["score"]
    #             if score_id != source_score_id:
    #                 continue
    #             resource_file = os.path.join(
    #                 "histograms", f"{score_id}.csv"
    #             )
    #             with resource.open_raw_file(resource_file) as infile:
    #                 df = pd.read_csv(infile, na_filter=False)
    #             assert set(df.columns) == set(["bars", "bins"]), \
    #                 "Incorrect CSV file"
    #             bins = df["bins"].values
    #             bars = list(map(float, filter(None, df["bars"].values)))
    #             hist.bins = bins
    #             hist.bars = bars

    #             return ScoreDesc(
    #                 resource.resource_id, source_score_id, selected_score_id,
    #                 hist, description)
    #         except KeyError:
    #             logger.error(
    #                 "Failed to load histogram of %s; "
    #                 "Couldn't find key %s", resource.resource_id, score_id,
    #                 exc_info=True)
    #         except AssertionError:
    #             logger.error(
    #                 "Incorrect configuration of %s; "
    #                 "histogram resource: %s", resource.resource_id, score_id,
    #                 exc_info=True)
    #         return None

    def get_scores(self):
        """Return all genomic scores histograms."""
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

    def __len__(self):
        return len(self.scores)
