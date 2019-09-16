import pytest

from io import StringIO
from contextlib import redirect_stdout
from box import Box

from dae.configuration.config_parser_base import VerificationError
from dae.gene.score_config_parser import ScoreConfigParser, \
    verify_impala_identifier

from dae.gene.tests.fixtures.impala_reserved_words import IMPALA_RESERVED_WORDS


def test_verifier_function_error_accumulation():
    value = ('123identifier-that-is-over-128-characters'
             'and_contains_multiple_errors_in_itttttttt'
             '$#)(Q$*)(#*$)#(*@)($*@#)($*@#)($*#@$()@#)'
             'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')

    expected_error_message = (
        "ERROR: The value '{}' must be between 1 and 128 symbols!\n"
        "ERROR: The value '{}' must only contain alphanumeric"
        " symbols and underscores!\n"
        "ERROR: The value '{}' must begin with an alphabetic character!\n"
    ).format(value, value, value)

    with pytest.raises(AssertionError) as excinfo:
        verify_impala_identifier(value)

    assert expected_error_message == str(excinfo.value)


def test_valid_identifier():
    config = ScoreConfigParser._verify_values(
        Box({'id': 'a_valid_123_identifier'})
    )
    assert len(config) == 1


def test_invalid_has_capital_letters():
    f = StringIO()
    conf = Box({'id': 'Invalid_HAS_CAPITAL_LETTERS'})
    with redirect_stdout(f):
        ScoreConfigParser._verify_values(conf)
    assert conf.id == 'invalid_has_capital_letters'
    assert ("WARNING: The value 'Invalid_HAS_CAPITAL_LETTERS'"
            " should be lowercase! Converting to lowercase...") in f.getvalue()


def test_invalid_starting_with_numeric():
    with pytest.raises(VerificationError):
        ScoreConfigParser._verify_values(
            Box({'id': '123_invalid_starting_with_numeric'})
        )


def test_invalid_starting_with_underscore():
    with pytest.raises(VerificationError):
        ScoreConfigParser._verify_values(
            Box({'id': '_invalid_starting_with_underscore'})
        )


def test_invalid_containing_hyphens():
    with pytest.raises(VerificationError):
        ScoreConfigParser._verify_values(
            Box({'id': 'invalid-identifier-contains-hyphens'})
        )


def test_invalid_containing_symbols():
    with pytest.raises(VerificationError):
        ScoreConfigParser._verify_values(
            Box({'id': '!@#$%^&*()-='})
        )


def test_invalid_too_short():
    with pytest.raises(VerificationError):
        ScoreConfigParser._verify_values(
            Box({'id': ''})
        )


def test_invalid_too_long():
    with pytest.raises(VerificationError):
        ScoreConfigParser._verify_values(
            Box({'id':
                ('identifier_that_is_over_128_characters___'
                 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
                 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
                 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')})
        )


def test_invalid_reserved_words():
    for reserved_word in IMPALA_RESERVED_WORDS:
        with pytest.raises(VerificationError):
            ScoreConfigParser._verify_values(
                Box({'id': reserved_word})
            )
            print("\nFAILED ON RESERVED WORD '{}'".format(reserved_word))


def test_invalid_reserved_words_non_lowercase():
    for reserved_word in IMPALA_RESERVED_WORDS:

        reserved_word = reserved_word.upper()

        with pytest.raises(VerificationError):
            ScoreConfigParser._verify_values(
                Box({'id': reserved_word})
            )
            print("\nFAILED ON CAPITAL-CASE RESERVED WORD '{}'"
                  .format(reserved_word))
