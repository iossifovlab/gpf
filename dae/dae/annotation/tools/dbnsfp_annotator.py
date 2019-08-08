import glob
import os.path
from dae.annotation.tools.score_annotator import NPScoreAnnotator


class dbNSFPAnnotator(NPScoreAnnotator):

    def __init__(self, config):
        self.current_chr = None
        self.dbNSFP_files = glob.glob(
                os.path.join(config.options.dbNSFP_path,
                             config.options.dbNSFP_filename))
        assert self.dbNSFP_files

        config.options.dbNSFP_filename = \
            config.options.dbNSFP_filename.replace('*', '{}')

        config.options.scores_config_file = os.path.join(
                config.options.dbNSFP_path,
                config.options.dbNSFP_config)
        config.options.scores_file = self.dbNSFP_files[0]

        super(dbNSFPAnnotator, self).__init__(config)

    def _init_score_file(self):
        if self.current_chr:
            self.config.options.scores_file = os.path.join(
                self.config.options.dbNSFP_path,
                self.config.options.dbNSFP_filename.format(self.current_chr))
            assert self.config.options.scores_file in self.dbNSFP_files
        super(dbNSFPAnnotator, self)._init_score_file()

    def do_annotate(self, aline, variant):
        if variant.chromosome != self.current_chr:
            self.current_chr = variant.chromosome
            self._init_score_file()
        super(dbNSFPAnnotator, self).do_annotate(aline, variant)
