from preloaded.register import Preload
from gene.scores import ScoreLoader


class Scores(Preload):

    def __init__(self):
        super(Scores, self).__init__()
        self.loader = ScoreLoader()
        self.desc = None

    def load(self):
        self.desc = self._load_desc()

    def is_loaded(self):
        self.desc is not None

    def get(self):
        return self

    def _load_desc(self):
        result = []
        for score_name in self.loader.scores:
            s = self.loader[score_name]
            assert s.df is not None

            result.append({
                'score': s.name,
                'desc': s.desc,
                'bars': s.values(),
                'bins': s.get_scores(),
                'xscale': s.xscale,
                'yscale': s.yscale
            })

        return result
