import pytest

from dae.variants.attributes import Sex


def test_sex_attribute():

    assert Sex.from_value(1) == Sex.male
    assert Sex.from_name("M") == Sex.male
    assert Sex.from_name("male") == Sex.male

    assert Sex.from_value(2) == Sex.female
    assert Sex.from_name("F") == Sex.female
    assert Sex.from_name("female") == Sex.female

    assert Sex.from_value(0) == Sex.unspecified
    assert Sex.from_name("U") == Sex.unspecified
    assert Sex.from_name("unspecified") == Sex.unspecified


def test_bad_sex_value():
    with pytest.raises(ValueError):
        Sex.from_value(100)


def test_bad_sex_name():
    with pytest.raises(ValueError):
        Sex.from_name("gaga")
