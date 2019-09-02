from dae.configuration.dae_config_parser import ConfigParserBase


class ScoreConfigParser(ConfigParserBase):

    CAST_TO_INT = (
        'bins',
    )

    SPLIT_STR_LISTS = (
        'range',
        'scores'
    )

    @classmethod
    def _get_genomic_scores(cls, genomic_scores):
        genomic_scores = super(ScoreConfigParser, cls).parse(genomic_scores)

        for genomic_score_id, genomic_score in genomic_scores.items():
            if not isinstance(genomic_score, dict):
                continue

            genomic_score['name'] = genomic_score_id
            genomic_score['id'] = genomic_score['name']
            genomic_score['range'] = genomic_score.get('range', None)

            if genomic_score['range']:
                genomic_score['range'] = \
                    tuple(map(float, genomic_score['range']))
            if genomic_score['help_filename']:
                with open(genomic_score['help_filename'], 'r') as f:
                    genomic_score['help'] = f.read()
            else:
                genomic_score['help'] = ''

        return genomic_scores

    @classmethod
    def parse(cls, config):
        config = super(ScoreConfigParser, cls).parse(config)

        config['genomicScores'] = \
            cls._get_genomic_scores(config['genomicScores'])

        return config
