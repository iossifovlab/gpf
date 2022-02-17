import pandas as pd


class Scores:
    def __init__(self, config, config_id):

        self.config = config
        self.genomic_values_col = "scores"

        self.id = config_id
        self.df = None
        self._dict = None

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

        if self.help_filename:
            with open(self.help_filename, "r") as infile:
                self.help = infile.read()
        else:
            self.help = None

        self._load_data()
        self.df.fillna(value=0, inplace=True)

    def _load_data(self):
        assert self.filename is not None

        df = pd.read_csv(self.filename)
        assert self.id in df.columns, "{} not found in {}".format(
            self.id, df.columns
        )
        self.df = df[[self.genomic_values_col, self.id]].copy()
        return self.df

    def values(self):
        return self.df[self.id].values

    def get_scores(self):
        return self.df["scores"].values


class ScoresFactory(object):
    def __init__(self, config):
        super(ScoresFactory, self).__init__()
        self.config = config

        self.scores = {}

        self._load()

    def get_scores(self):
        result = []

        for score in self.scores.values():
            assert score.df is not None
            result.append(score)

        return result

    def _load(self):
        if not self.config:
            return
        for score_id, score_config in self.config.genomic_scores.items():
            s = Scores(score_config, score_id)
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
