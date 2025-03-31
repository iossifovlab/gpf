import logging

import numpy as np

logger = logging.getLogger(__name__)

DEEPSEA_MAPPING = {
    "A": np.array([1, 0, 0, 0]).T,
    "G": np.array([0, 1, 0, 0]).T,
    "C": np.array([0, 0, 1, 0]).T,
    "T": np.array([0, 0, 0, 1]).T,
    "N": np.array([0, 0, 0, 0]).T,
}


SPLICE_AI_MAPPING: dict[str, np.ndarray] = {
    "A": np.array([1, 0, 0, 0], np.int8),
    "C": np.array([0, 1, 0, 0], np.int8),
    "G": np.array([0, 0, 1, 0], np.int8),
    "T": np.array([0, 0, 0, 1], np.int8),
    "N": np.array([0, 0, 0, 0], np.int8),
}


MAPPING = SPLICE_AI_MAPPING


def one_hot_encode(
    seq: str,
) -> np.ndarray:
    """One-hot encode a DNA sequence."""
    assert isinstance(seq, str), seq

    result = np.zeros((len(seq), 4), np.int8)
    for seq_index, nucleotide in enumerate(seq):
        if nucleotide not in {"N", "A", "C", "G", "T"}:
            logger.warning(
                "unexpected nucleotied %s in pos %s at %s:",
                nucleotide, seq_index, seq)

        result[seq_index, :] = MAPPING.get(nucleotide, MAPPING["N"])
    return result


def one_hot_decode(
    seq: np.ndarray,
) -> str:
    """One-hot decode a DNA sequence."""
    result = seq.shape[0] * ["N"]
    alphabet = list(MAPPING.keys())
    for seq_index in range(len(seq)):
        one_hot_nucleotide = list(seq[seq_index, :])
        assert len(one_hot_nucleotide) == 4

        if 1 not in one_hot_nucleotide:
            result[seq_index] = "N"
        else:
            index = one_hot_nucleotide.index(1)
            result[seq_index] = alphabet[index]
    return "".join(result)
