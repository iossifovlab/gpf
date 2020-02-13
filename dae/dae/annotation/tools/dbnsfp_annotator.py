import glob
import os.path
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.annotation.tools.score_annotator import NPScoreAnnotator


class dbNSFPAnnotator(NPScoreAnnotator):
    def __init__(self, config, genomes_db):
        self.current_chr = None
        self.dbNSFP_files = glob.glob(
                os.path.join(config.options.dbNSFP_path,
                             config.options.dbNSFP_filename))
        assert self.dbNSFP_files

        options = config.options

        if options.dbNSFP_filename:
            options = GPFConfigParser.modify_tuple(
                options, {
                    "dbNSFP_filename": options.dbNSFP_filename.replace('*', '{}')
                }
            )

        scores_config_file = os.path.join(
                config.options.dbNSFP_path,
                config.options.dbNSFP_config)
        options = GPFConfigParser.modify_tuple(
            options, {"scores_config_file": scores_config_file}
        )
        options = GPFConfigParser.modify_tuple(
            options, {"scores_file": self.dbNSFP_files[0]}
        )
        config = GPFConfigParser.modify_tuple(
            config, {"options": options}
        )

        super(dbNSFPAnnotator, self).__init__(config, genomes_db)

    def _init_score_file(self):
        if self.current_chr:
            options = self.config.options
            scores_file = os.path.join(
                self.config.options.dbNSFP_path,
                self.config.options.dbNSFP_filename.format(self.current_chr))
            options = GPFConfigParser.modify_tuple(
                options, {"scores_file": scores_file}
            )
            self.config = GPFConfigParser.modify_tuple(
                self.config, {"options": options}
            )
            assert self.config.options.scores_file in self.dbNSFP_files
        super(dbNSFPAnnotator, self)._init_score_file()

    def do_annotate(self, aline, variant):
        if variant.chromosome != self.current_chr:
            self.current_chr = variant.chromosome
            self._init_score_file()
        super(dbNSFPAnnotator, self).do_annotate(aline, variant)
