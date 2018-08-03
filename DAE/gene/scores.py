import ConfigParser
from box import Box
from collections import OrderedDict

from genomic_values import GenomicValues
from Config import Config
import common.config


class Scores(GenomicValues):
    def __init__(self, scores_name, config, *args, **kwargs):
        super(Scores, self).__init__('genomicScores.{}'.format(scores_name),
                                     *args, **kwargs)

        self.config = config
        self.genomic_values_col = 'scores'

        self.desc = self.config[self.section_name].desc
        self.bins = int(self.config[self.section_name].bins)
        self.xscale = self.config[self.section_name].xscale
        self.yscale = self.config[self.section_name].yscale
        self.filename = self.config[self.section_name].file
        if self.config[self.section_name].range:
            self.range = tuple(map(
                float, self.config[self.section_name].range.split(',')))
        else:
            self.range = None

        self._load_data()

    def get_scores(self):
        return self.df['scores'].values


class ScoreLoader(object):

    def __init__(self, *args, **kwargs):
        super(ScoreLoader, self).__init__(*args, **kwargs)
        self.daeConfig = Config()

        config = ConfigParser.SafeConfigParser({
            'wd': self.daeConfig.daeDir
        })
        config.optionxform = str
        config.read(self.daeConfig.genomicScoresDBconfFile)
        self.config = Box(common.config.to_dict(config),
                          default_box=True, default_box_attr=None)

        self.scores = OrderedDict()

        self._load()

    def _load(self):
        scores = self.config.genomicScores.scores
        names = [s.strip() for s in scores.split(',')]
        for name in names:
            s = Scores(name, self.config)
            self.scores[name] = s

    def __getitem__(self, score_name):
        if score_name not in self.scores:
            raise KeyError()

        res = self.scores[score_name]
        if res.df is None:
            res.load_scores()
        return res

    def __contains__(self, score_name):
        return score_name in self.scores
