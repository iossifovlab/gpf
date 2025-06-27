import pytest
from dae.variants.attributes import Sex


def test_sex_attribute() -> None:

    assert Sex.from_value(1) == Sex.male
    assert Sex.from_name("M") == Sex.male
    assert Sex.from_name("male") == Sex.male

    assert Sex.from_value(2) == Sex.female
    assert Sex.from_name("F") == Sex.female
    assert Sex.from_name("female") == Sex.female

    assert Sex.from_value(0) == Sex.unspecified
    assert Sex.from_name("U") == Sex.unspecified
    assert Sex.from_name("unspecified") == Sex.unspecified


def test_bad_sex_value() -> None:
    with pytest.raises(ValueError, match="100 is not a valid Sex"):
        Sex.from_value(100)


def test_bad_sex_name() -> None:
    with pytest.raises(ValueError, match="unexpected sex name: gaga"):
        Sex.from_name("gaga")
