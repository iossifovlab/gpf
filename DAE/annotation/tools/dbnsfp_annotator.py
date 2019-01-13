from os import listdir
import os.path
from annotation.tools.score_annotator import NPScoreAnnotator


class dbNSFPAnnotator(NPScoreAnnotator):

    def __init__(self, config):
        self.current_chr = None
        self.dbNSFP_files = self._get_dbNSFP_files(
                config.options.dbNSFP_path,
                config.options.dbNSFP_filename)
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

    def _get_dbNSFP_files(self, path, wildcard):
        files = []
        wildcard = wildcard.split('*')
        for f in listdir(path):
            if not os.path.isfile(os.path.join(path, f)):
                continue
            if f[:len(wildcard[0])] == wildcard[0] and \
               f[len(f)-len(wildcard[1]):] == wildcard[1]:
                    files.append(os.path.join(path, f))
        return files

    def do_annotate(self, aline, variant):
        if variant.chromosome != self.current_chr:
            self.current_chr = variant.chromosome
            self._init_score_file()
        super(dbNSFPAnnotator, self).do_annotate(aline, variant)
