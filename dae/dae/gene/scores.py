from collections import OrderedDict

from dae.gene.genomic_values import GenomicValues


class Scores(GenomicValues):
    def __init__(self, config, *args, **kwargs):
        super(Scores, self).__init__(config.name, *args, **kwargs)

        self.config = config
        self.genomic_values_col = 'scores'

        self.desc = self.config.desc
        self.bins = self.config.bins
        self.xscale = self.config.xscale
        self.yscale = self.config.yscale
        self.filename = self.config.file
        self.help_filename = self.config.help_file
        if self.config.range:
            self.range = tuple(map(float, self.config.range))
        else:
            self.range = None
        if self.help_filename:
            with open(self.help_filename, 'r') as f:
                self.help = f.read()
        else:
            self.help = ''

        self._load_data()
        self.df.fillna(value=0, inplace=True)

    def get_scores(self):
        return self.df['scores'].values


class ScoreLoader(object):

    def __init__(self, config, *args, **kwargs):
        super(ScoreLoader, self).__init__(*args, **kwargs)
        self.config = config

        self.scores = OrderedDict()

        self._load()

    def get_scores(self):
        result = []

        for _, score in self.scores.items():
            assert score.df is not None
            result.append(score)

        return result

    def _load(self):
        print(self.config.genomic_scores.scores)
        for score_name in self.config.genomic_scores.scores:
            print(self.config.scores)
            print(score_name)
            score_config = self.config.scores.get(score_name)
            print(score_config)
            s = Scores(score_config)
            self.scores[score_name] = s

    def __getitem__(self, score_name):
        if score_name not in self.scores:
            raise KeyError()

        res = self.scores[score_name]
        if res.df is None:
            res.load_scores()
        return res

    def __contains__(self, score_name):
        return score_name in self.scores
