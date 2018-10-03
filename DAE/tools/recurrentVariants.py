#!/usr/bin/env python

from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
import sys
import argparse
from DAE import vDB
from itertools import groupby
from collections import Counter


def sort_by_family_id(x):
    return x.familyId


def get_families(prb_LGDs):
    sorted_families = sorted(prb_LGDs, key=sort_by_family_id)
    sorted_families_dict = {k: list(g) for k, g in
                            groupby(sorted_families, key=sort_by_family_id)}
    return sorted_families_dict


def list_variants_by_families(prb_LGDs):
    for family_id, variants in get_families(prb_LGDs).items():
        if len(variants) == 1:
            continue
        print('The proband of family {} has {} LGD variants'
              .format(family_id, len(variants)))
        for v in variants:
            effects = '|'.join([x['sym'] + ':' + x['eff']
                                for x in v.requestedGeneEffects])
            line = [v.study.name, v.location, v.variant,
                    v.atts['inChild'], effects]
            print('\t' + '\t'.join(line))


# test for recurrence in the same proband
def recurrence_in_proband(prb_LGDs):
    ccs = Counter([str(v.familyId) + ':' + ge['sym'] for v in prb_LGDs
                   for ge in v.requestedGeneEffects])
    for fgs in ccs:
        if ccs[fgs] > 1:
            print('WARNING: {} is seen {} times'.format(fgs, ccs[fgs]))


def parse_cli_studies():
    parser = argparse.ArgumentParser(
        description='Recurrent Variants')

    parser.add_argument('studies')
    args = parser.parse_args(sys.argv[1:])
    return args.studies


def get_symbols2variants(prb_LGDs):
    gn_sorted = sorted([[ge['sym'], v.familyId, v.location, v]
                        for v in prb_LGDs for ge in v.requestedGeneEffects])
    return {sym: [t[3] for t in tpi] for sym, tpi
            in groupby(gn_sorted, key=lambda x: x[0])}


def get_effect(v, sym):
    effect = ''
    for gene_effects in v.requestedGeneEffects:
        if gene_effects['sym'] == sym:
            effect = gene_effects['eff']
    if effect == '':
        raise Exception('breh')
    return effect


if __name__ == '__main__':
    study_names = parse_cli_studies()
    studies = vDB.get_studies(study_names)
    prb_LGDs = list(vDB.get_denovo_variants(
                    studies, inChild='prb', effectTypes="LGDs"))

    print('There are {} variants in probands'.format(len(prb_LGDs)))
    list_variants_by_families(prb_LGDs)
    recurrence_in_proband(prb_LGDs)

    symbols2variants = get_symbols2variants(prb_LGDs)
    symbols2families_len = {sym: len(set([v.familyId for v in vs]))
                            for sym, vs in symbols2variants.items()}
    symbols2families_len_sorted = sorted(
        symbols2families_len.items(), key=lambda x: (x[1], x[0]))

    for sym, families_len in symbols2families_len_sorted:
        print(sym + '\t' + str(families_len), end='\t')

        effects_dict = dict()
        for v in symbols2variants[sym]:
            effects_dict[v.familyId] = ';'.join(
                [v.study.name, get_effect(v, sym)[0], v.atts['inChild'][3]])

        for f_id in sorted(effects_dict.keys()):
            print(str(f_id) + ':' + effects_dict[f_id], end='\t')
        print()

    recurrence_counter = Counter(symbols2families_len.values())
    families = set([f for s in studies for f in s.families])
    print('The recurrence in {} probands'.format(len(families)))
    print('hits\tgeneNumber')
    for hn, cnt in sorted(recurrence_counter.items(), key=lambda x: x[1]):
        print(hn, '\t', cnt)
