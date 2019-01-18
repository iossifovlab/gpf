from os import listdir
import os.path
import re
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

    @staticmethod
    def _wildcard_to_regex(wildcard):
        assert wildcard
        if wildcard[0] != '*':
            wildcard = r'^{}'.format(wildcard)
        if wildcard[-1] != '*':
            wildcard = r'{}\Z'.format(wildcard)
        return wildcard.split('*')

    @staticmethod
    def _search_wildcard(inp, wildcard):
        wildcards = dbNSFPAnnotator._wildcard_to_regex(wildcard)
        for regex_token in wildcards:
            if re.compile(regex_token).search(inp) is None:
                return False
        return True

    def _get_dbNSFP_files(self, path, wildcard):
        files = []
        for file_ in listdir(path):
            if not os.path.isfile(os.path.join(path, file_)):
                continue
            if dbNSFPAnnotator._search_wildcard(file_, wildcard):
                files.append(os.path.join(path, file_))
        return files

    def do_annotate(self, aline, variant):
        if variant.chromosome != self.current_chr:
            self.current_chr = variant.chromosome
            self._init_score_file()
        super(dbNSFPAnnotator, self).do_annotate(aline, variant)
