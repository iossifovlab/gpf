from dae.configuration.config_parser_base import ConfigParserBase
from dae.configuration.utils import IMPALA_RESERVED_WORDS


def verify_impala_identifier(value):
    errs = []
    errmsg = "ERROR: The value '{}' ".format(value)

    if not isinstance(value, str):
        errs.append(errmsg + "must be of type str, not {}!"
                    .format(type(value)))
    if not 1 < len(value) < 128:
        errs.append(errmsg + "must be between 1 and 128 symbols!")
    if not value.isascii():
        errs.append(errmsg + "must be ASCII!")
    if not value.replace('_', '').isalnum():
        errs.append(errmsg + ("must only contain alphanumeric"
                              " symbols and underscores!"))
    if not value[0].isalpha():
        errs.append(errmsg + ("must begin with an"
                              " alphabetic character!"))

    if value.lower() in IMPALA_RESERVED_WORDS:
        errs.append(errmsg + "is an Impala reserved word!")

    assert not errs, '\n'.join(errs) + '\n'

    if not value.islower():
        print(("WARNING: The value '{}' should be lowercase!"
               " Converting to lowercase...").format(value))
        value = value.lower()

    return value


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

    VERIFY_VALUES = {
        'id': verify_impala_identifier
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
