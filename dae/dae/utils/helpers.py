import os
from functools import partial
import numpy as np
import pandas as pd
from dae.pedigrees.pedigree_reader import PedigreeReader
from dae.utils.dae_utils import dae2vcf_variant
from dae.utils.vcf_utils import str2mat, GENOTYPE_TYPE
from dae.pedigrees.family import FamiliesData


def pedigree_from_path(filepath, family_format='pedigree'):
    if family_format == 'pedigree':
        ped_df = PedigreeReader.load_pedigree_file(filepath)
    elif family_format == 'simple':
        ped_df = PedigreeReader.load_simple_family_file(filepath)
    else:
        raise NotImplementedError(
            'unsupported file format:' + family_format)

    study_id = os.path.splitext(os.path.basename(filepath))[0]
    return ped_df, study_id


def split_location(location):
    assert ':' in location
    chrom, pos = location.split(':')
    return chrom, pos


def add_flexible_denovo_import_args(parser):
    parser.add_argument(
        '--denovo-sep',
        help='The separator dividing the columns in the denovo file.',
        default=','
    )
    parser.add_argument(
        '--denovo-location',
        help=('The label or index of the column containing the CSHL-style'
              ' location of the variant.'),
    )
    parser.add_argument(
        '--denovo-variant',
        help=('The label or index of the column containing the CSHL-style'
              ' representation of the variant.'),
    )
    parser.add_argument(
        '--denovo-chrom',
        help=('The label or index of the column containing the chromosome'
              ' upon which the variant is located.'),
    )
    parser.add_argument(
        '--denovo-pos',
        help=('The label or index of the column containing the position'
              ' upon which the variant is located.'),
    )
    parser.add_argument(
        '--denovo-ref',
        help=('The label or index of the column containing the reference'
              ' allele for the variant.'),
    )
    parser.add_argument(
        '--denovo-alt',
        help=('The label or index of the column containing the alternative'
              ' allele for the variant.'),
    )
    parser.add_argument(
        '--denovo-personId',
        help='The label or index of the column containing the person\'s ID.',
    )
    parser.add_argument(
        '--denovo-familyId',
        help='The label or index of the column containing the family\'s ID.',
    )
    parser.add_argument(
        '--denovo-genotype',
        help=('The label or index of the column containing the best state'
              ' for the family.'),
    )


def produce_genotype(family, members_with_variant):
    genotype = np.zeros(len(family) * 2, dtype=GENOTYPE_TYPE)
    members_with_variant_index = family.members_index(members_with_variant)
    for index in members_with_variant_index:
        genotype[(index * 2) + 1] = 1
    return genotype


def read_variants_from_dsv(
    filepath,
    genome,
    sep='\t',
    location=None,
    variant=None,
    chrom=None,
    pos=None,
    ref=None,
    alt=None,
    personId=None,
    familyId=None,
    genotype=None,
    families=None
):
    """
    Read a text file containing variants in the form
    of delimiter-separted values and produce a dataframe.

    The text file may use different names for the columns
    containing the relevant data - these are specified
    with the provided parameters.

    :param str filepath: The path to the DSV file to read.

    :param genome: A genome object.

    :param str location: The label or index of the column containing the
    CSHL-style location of the variant.

    :param str variant: The label or index of the column containing the
    CSHL-style representation of the variant.

    :param str chrom: The label or index of the column containing the
    chromosome upon which the variant is located.

    :param str pos: The label or index of the column containing the position
    upon which the variant is located.

    :param str ref: The label or index of the column containing the variant's
    reference allele.

    :param str alt: The label or index of the column containing the variant's
    alternative allele.

    :param str personId: The label or index of the column containing either a
    singular person ID or a comma-separated list of person IDs.

    :param str familyId: The label or index of the column containing a
    singular family ID.

    :param str genotype: The label or index of the column containing the best
    state for the variant.

    :param str families: An instance of the FamiliesData class for the pedigree
    of the relevant study.

    :type genome: An instance of GenomicSequence_Dan or GenomicSequence_Ivan.

    :return: Dataframe containing the variants, with the following header -
    'chrom', 'position', 'reference', 'alternative', 'family_id', 'genotype'.

    :rtype: An instance of Pandas' DataFrame class.
    """
    assert location or (chrom and pos),\
        ('You must specify either a location column or'
         ' chromosome and position columns!')
    assert variant or (ref and alt), \
        ('You must specify either a variant column or'
         ' reference and alternative columns!')
    assert (personId and families) or (familyId and genotype), \
        ('You must specify either a personId column and provide a FamiliesData'
         ' object or specify familyId and genotype columns!')

    if families:
        assert isinstance(families, FamiliesData), \
            'families must be an instance of FamiliesData!'

    raw_df = pd.read_csv(
        filepath,
        sep=sep,
        dtype={
            chrom: str,
            pos: str,
            personId: str,
            familyId: str,
            genotype: str,
        }
    )

    if location:
        chrom_col, pos_col = zip(*map(split_location, raw_df[location]))
    else:
        chrom_col = raw_df.loc[:, chrom]
        pos_col = raw_df.loc[:, pos]

    if variant:
        assert genome, 'You must provide a genome object!'
        variant_col = raw_df.loc[:, variant]
        ref_alt_tuples = [
            dae2vcf_variant(*variant_tuple, genome)
            for variant_tuple
            in zip(chrom_col, pos_col, variant_col)
        ]
        _, ref_col, alt_col = zip(*ref_alt_tuples)

    else:
        ref_col = raw_df.loc[:, ref]
        alt_col = raw_df.loc[:, alt]

    if personId:
        temp_df = pd.DataFrame({
            'chrom': chrom_col,
            'pos': pos_col,
            'ref': ref_col,
            'alt': alt_col,
            'personId': raw_df.loc[:, personId],
        })

        variant_to_people = dict()
        variant_to_families = dict()

        for variant, variants_indices in \
                temp_df.groupby(['chrom', 'pos', 'ref', 'alt']).groups.items():
            # Here we join and then split again by ',' to handle cases
            # where the person IDs are actually a list of IDs, separated
            # by a ','
            people = ','.join(
                temp_df.iloc[variants_indices].loc[:, 'personId']).split(',')

            variant_to_people[variant] = people
            variant_to_families[variant] = \
                families.families_query_by_person(people)

        # TODO Implement support for multiallelic variants
        result = []
        for variant, families in variant_to_families.items():
            for family_id, family in families.items():
                result.append({
                    'chrom': variant[0],
                    'position': variant[1],
                    'reference': variant[2],
                    'alternative': variant[3],
                    'family_id': family_id,
                    'genotype': produce_genotype(
                        family, variant_to_people[variant]
                    )
                })

        return pd.DataFrame(result)

    else:
        family_col = raw_df.loc[:, familyId]
        str2mat_partial = partial(str2mat, col_sep=' ')

        genotype_col = [
            np.ndarray.flatten(person_genotype, order='F')
            for person_genotype
            in map(str2mat_partial, raw_df[genotype])
        ]

    return pd.DataFrame({
        'chrom': chrom_col,
        'position': pos_col,
        'reference': ref_col,
        'alternative': alt_col,
        'family_id': family_col,
        'genotype': genotype_col,
    })
