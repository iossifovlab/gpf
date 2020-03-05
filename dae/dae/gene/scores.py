from collections import OrderedDict

from dae.gene.genomic_values import GenomicValues


class Scores(GenomicValues):
    def __init__(self, config):
        super(Scores, self).__init__(config.id)

        self.config = config
        self.genomic_values_col = "scores"

        self.desc = self.config.desc
        self.bins = self.config.bins
        self.xscale = self.config.xscale
        self.yscale = self.config.yscale
        self.filename = self.config.file
        self.help_filename = self.config.help_file
        if self.config.range:
            self.range = (self.config.range.start, self.config.range.end)
        else:
            self.range = None
        self.help = self.config.help

        self._load_data()
        self.df.fillna(value=0, inplace=True)

    def get_scores(self):
        return self.df["scores"].values


class ScoresFactory(object):
    def __init__(self, config):
        super(ScoresFactory, self).__init__()
        self.config = config

        self.scores = OrderedDict()

        self._load()

    def get_scores(self):
        result = []

        for score in self.scores.values():
            assert score.df is not None
            result.append(score)

        return result

    def _load(self):
        for score_config in self.config.genomic_scores:
            s = Scores(score_config)
            if s.id in self.config.scores:
                self.scores[score_config.id] = s

    def __getitem__(self, score_id):
        if score_id not in self.scores:
            raise KeyError()

        res = self.scores[score_id]
        if res.df is None:
            res.load_scores()
        return res

    def __contains__(self, score_id):
        return score_id in self.scores
