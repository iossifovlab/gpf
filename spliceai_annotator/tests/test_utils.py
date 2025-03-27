from spliceai.utils import one_hot_encode as one_hot_encode_spliceai

from spliceai_annotator.utils import (
    one_hot_decode,
    one_hot_encode,
)


def test_one_hot_encode() -> None:
    seq = "ACGTN"
    encoded = one_hot_encode(seq)
    expected = one_hot_encode_spliceai(seq)
    assert encoded.shape == expected.shape
    assert (encoded == expected).all()


def test_one_hot_decode() -> None:
    seq = "ACGTN"
    encoded = one_hot_encode(seq)
    result = one_hot_decode(encoded)
    assert result == seq
