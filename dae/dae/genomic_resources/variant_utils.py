import itertools
import logging

from dae.genomic_resources.reference_genome import (
    ReferenceGenome,
)

logger = logging.getLogger(__name__)


def normalize_variant(
    chrom: str,
    pos: int,
    ref: str,
    alts: list[str],
    genome: ReferenceGenome,
) -> tuple[str, int, str, list[str]]:
    """Normalize a variant.

    Using algorithm defined in
    the https://genome.sph.umich.edu/wiki/Variant_Normalization
    """

    while True:
        changed = False
        logger.debug("normalizing variant: %s:%d %s>%s", chrom, pos, ref, alts)

        if len(ref) > 0 and all(len(alt) > 0
                and ref[-1] == alt[-1] for alt in alts):
            logger.debug(
                "shrink from right: %s:%d %s>%s", chrom, pos, ref, alts)
            if all(ref == alt for alt in alts) and len(ref) == 1:
                logger.info(
                    "no variant: %s:%d %s>%s", chrom, pos, ref, alts)
            else:
                ref = ref[:-1]
                alts = [alt[:-1] for alt in alts]
                changed = True

        if pos > 1 and (
                len(ref) == 0 or
                any(len(alt) == 0 for alt in alts)):
            logger.debug(
                "moving left variant: %s:%d %s>%s", chrom, pos, ref, alts)
            left = genome.get_sequence(
                chrom, pos - 1, pos - 1)
            pos -= 1
            ref = f"{left}{ref}"
            alts = [f"{left}{alt}" for alt in alts]
            changed = True

        if not changed:
            break

    while len(ref) >= 2 and all(len(alt) >= 2
            and ref[0] == alt[0] for alt in alts):
        pos += 1
        ref = ref[1:]
        alts = [alt[1:] for alt in alts]

    return chrom, pos, ref, alts


def maximally_extend_variant(
    chrom: str,
    pos: int,
    ref: str,
    alts: list[str],
    genome: ReferenceGenome,
) -> tuple[str, int, str, list[str]]:
    """Maximally extend a variant."""
    chrom, pos, ref, alts = normalize_variant(chrom, pos, ref, alts, genome)
    if not all(alt[0] == ref[0] for alt in alts):
        left = genome.get_sequence(chrom, pos - 1, pos - 1)
        pos -= 1
        ref = f"{left}{ref}"
        alts = [f"{left}{alt}" for alt in alts]
    if not all(alt[-1] == ref[-1] for alt in alts):
        right = genome.get_sequence(chrom, pos + len(ref), pos + len(ref))
        ref = f"{ref}{right}"
        alts = [f"{alt}{right}" for alt in alts]
    while True:
        changed = False
        for (s1, s2) in itertools.pairwise([ref, *alts]):
            if len(s1) > len(s2):
                s1, s2 = s2, s1
            if s2.startswith(s1) or s2.endswith(s1):
                right = genome.get_sequence(
                    chrom, pos + len(ref), pos + len(ref))
                ref = f"{ref}{right}"
                alts = [f"{alt}{right}" for alt in alts]
                changed = True
                break
        if not changed:
            break
    return chrom, pos, ref, alts
