from dae.configuration.dae_config_parser import DAEConfigParser


class classproperty(property):
    def __get__(self, obj, objtype=None):
        return super(classproperty, self).__get__(objtype)


class ScoreConfigParser(DAEConfigParser):

    CAST_TO_INT = (
        'bins',
    )

    SPLIT_STR_LISTS = (
        'range',
        'scores'
    )

    @classproperty
    def PARSE_TO_LIST(cls):
        return {
            'scores': {
                'group': 'genomicScores',
                'getter': cls._get_genomic_score,
            }
        }

    CONVERT_LIST_TO_DICT = (
        'scores',
    )

    @staticmethod
    def _get_genomic_score(genomic_score_type, genomic_score_options, config):
        gs_config = config.get(genomic_score_type, None)
        genomic_score = {}

        genomic_score['name'] = genomic_score_type.split('.')[-1]
        genomic_score['id'] = genomic_score['name']
        genomic_score['file'] = gs_config.get('file', None)
        genomic_score['desc'] = gs_config.get('desc', None)
        genomic_score['file'] = gs_config.get('file', None)
        genomic_score['bins'] = gs_config.get('bins', None)
        genomic_score['yscale'] = gs_config.get('yscale', None)
        genomic_score['xscale'] = gs_config.get('xscale', None)
        genomic_score['range'] = gs_config.get('range', None)
        genomic_score['help_file'] = gs_config.get('help_file', None)

        yield genomic_score

    @classmethod
    def parse(cls, config):
        config = super(ScoreConfigParser, cls).parse(config)
        config = super(ScoreConfigParser, cls).parse_section(config)

        return config
