import os.path
from annotation.tools.score_annotator import NPScoreAnnotator


class dbNSFPAnnotator(NPScoreAnnotator):

    chr_map = {'22': 'X', '23': 'Y'}

    def __init__(self, config):
        self.current_chr = '1'
        config.options.scores_config_file = os.path.join(
                config.options.dbNSFP_path,
                config.options.dbNSFP_config)
        super(dbNSFPAnnotator, self).__init__(config)

    def _init_score_file(self):
        if self.current_chr in self.chr_map:
            self.current_chr = self.chr_map[self.current_chr]
        self.config.options.scores_file = os.path.join(
                self.config.options.dbNSFP_path,
                self.config.options.dbNSFP_filename.format(self.current_chr))
        super(dbNSFPAnnotator, self)._init_score_file()

    def do_annotate(self, aline, variant):
        if variant.chromosome != self.current_chr:
            self.current_chr = variant.chromosome
            self._init_score_file()
        super(dbNSFPAnnotator, self).do_annotate(aline, variant)
