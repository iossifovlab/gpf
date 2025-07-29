from dae.utils.variant_utils import reverse_complement
from spliceai_annotator.utils import (
    one_hot_decode,
    one_hot_encode,
)


def test_one_hot_decode() -> None:
    seq = "ACGTN"
    encoded = one_hot_encode(seq)
    result = one_hot_decode(encoded)
    assert result == seq


def test_one_hot_encode_reverse() -> None:
    seq = "ACGTN"
    encoded = one_hot_encode(seq)
    rev_encode = one_hot_encode(reverse_complement(seq))
    assert encoded.shape == rev_encode.shape
    assert (encoded[::-1, ::-1] == rev_encode).all()
