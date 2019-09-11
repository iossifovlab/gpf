from dae.configuration.config_parser_base import ConfigParserBase


class ScoreConfigParser(ConfigParserBase):

    CAST_TO_INT = (
        'bins',
    )

    SPLIT_STR_LISTS = (
        'range',
        'scores'
    )

    FILTER_SELECTORS = {
        'genomicScores': 'selected_genomic_score_values',
    }

    @classmethod
    def _parse_genomic_scores(cls, genomic_scores):
        genomic_scores = super(ScoreConfigParser, cls).parse(genomic_scores)
        if not genomic_scores:
            genomic_scores = {}

        for genomic_score in genomic_scores.values():
            if genomic_score.range:
                genomic_score.range = tuple(map(float, genomic_score.range))
            if genomic_score.help_filename:
                with open(genomic_score.help_filename, 'r') as f:
                    genomic_score.help = f.read()
            else:
                genomic_score.help = ''

        return genomic_scores

    @classmethod
    def parse(cls, config):
        config = super(ScoreConfigParser, cls).parse(config)
        if config is None:
            return None

        selected_genomic_score_values = config.genomic_scores.scores
        config.selected_genomic_score_values = selected_genomic_score_values
        config = super(ScoreConfigParser, cls).parse_section(config)

        config.genomic_scores = \
            cls._parse_genomic_scores(config.genomic_scores)

        return config
