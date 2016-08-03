'''
Created on Jun 8, 2015

@author: lubo
'''
import cPickle
import cStringIO
from collections import Counter
import csv
import os
from scipy import stats
from sets import ImmutableSet
import zlib

from django.conf import settings
from django.core.cache import caches

from DAE import vDB
import numpy as np
import pandas as pd

from precompute.register import Precompute


def _collect_affected_gene_syms(vs):
    return [set([ge['sym'] for ge in v.requestedGeneEffects])
            for v in vs]


def _collect_unique_gene_syms(affected_gene_sets):
    gene_set = set()
    for gs in affected_gene_sets:
        gene_set |= set(gs)
    return gene_set


def _count_gene_syms(affected_gene_sets):
    background = Counter()
    for gene_set in affected_gene_sets:
        for gene_sym in gene_set:
            background[gene_sym] += 1
    return background


def _build_synonymous_background(transmitted_study_name):
    transmitted_study = vDB.get_study(transmitted_study_name)
    vs = transmitted_study.get_transmitted_summary_variants(
        ultraRareOnly=True,
        minParentsCalled=600,
        effectTypes=["synonymous"])
    affected_gene_syms = _collect_affected_gene_syms(vs)

    base = [gs for gs in affected_gene_syms if len(gs) == 1]
    foreground = [gs for gs in affected_gene_syms if len(gs) > 1]

    base_counts = _count_gene_syms(base)

    base_sorted = sorted(zip(base_counts.keys(),
                             base_counts.values()))

    b = np.array(base_sorted,
                 dtype=[('sym', '|S32'), ('raw', '>i4')])

    return (b, foreground)


class Background(object):

    def __init__(self):
        self.background = None
        self.background_cache = caches['enrichment']
        self.name = None

    @property
    def is_ready(self):
        return self.background is not None

    def _prob(self, gene_syms):
        return 1.0 * self._count(gene_syms) / self._total

    def cache_key(self, gene_syms):
        gskey = hash(ImmutableSet(gene_syms))
        key = hash(self.name + str(gskey))
        return key

    def cache_get(self, gene_syms):
        key = self.cache_key(gene_syms)
        value = self.background_cache.get(key)
        return value

    def cache_store(self, gene_syms, base):
        key = self.cache_key(gene_syms)
        self.background_cache.set(key, base, 30)

    def _count(self, gen_syms):
        vpred = np.vectorize(lambda sym: sym in gen_syms)
        index = vpred(self.background['sym'])
        return np.sum(self.background['raw'][index])

    def test(self, O, N, effect_type, gene_syms, boys=0, girls=0):
        # N = total
        bg_prob = self._prob(gene_syms)
        expected = round(bg_prob * N, 4)
        p_val = stats.binom_test(O, N, p=bg_prob)
        return expected, p_val


class SynonymousBackground(Background, Precompute):
    TRANSMITTED_STUDY_NAME = 'w1202s766e611'

    def __init__(self):
        super(SynonymousBackground, self).__init__()
        self.name = 'synonymousBackgroundModel'

    def precompute(self):
        self.background, self.foreground = \
            _build_synonymous_background(self.TRANSMITTED_STUDY_NAME)
        return self.background

    def _count_foreground_events(self, gene_syms):
        count = 0
        for gs in self.foreground:
            touch = False
            for sym in gs:
                if sym in gene_syms:
                    touch = True
                    break
            if touch:
                count += 1
        return count

    def _count(self, gene_syms):
        res = self.cache_get(gene_syms)
        if not res:
            vpred = np.vectorize(lambda sym: sym in gene_syms)
            index = vpred(self.background['sym'])
            base = np.sum(self.background['raw'][index])
            foreground = self._count_foreground_events(gene_syms)
            res = base + foreground
            self.cache_store(gene_syms, res)
        return res

    @property
    def _total(self):
        return np.sum(self.background['raw']) + len(self.foreground)

    def serialize(self):
        fout = cStringIO.StringIO()
        np.save(fout, self.background)

        b = zlib.compress(fout.getvalue())
        f = zlib.compress(cPickle.dumps(self.foreground))
        return {'background': b,
                'foreground': f}

    def deserialize(self, data):
        b = data['background']
        fin = cStringIO.StringIO(zlib.decompress(b))
        self.background = np.load(fin)

        f = data['foreground']
        self.foreground = cPickle.loads(zlib.decompress(f))


class CodingLenBackground(Background, Precompute):
    FILENAME = os.path.join(
        settings.BASE_DIR,
        '..',
        'data/enrichment/background-model-coding-len-in-target.csv')

    def _load_and_prepare_build(self):
        back = []
        with open(self.FILENAME, 'r') as f:
            reader = csv.reader(f)
            reader.next()
            for row in reader:
                back.append((str(row[0]), int(row[1])))
        return back

    def __init__(self):
        super(CodingLenBackground, self).__init__()
        self.name = 'codingLenBackgroundModel'

    def precompute(self):
        back = self._load_and_prepare_build()
        self.background = np.array(
            back,
            dtype=[('sym', '|S32'), ('raw', '>i4')])
        return self.background

    def serialize(self):
        fout = cStringIO.StringIO()
        np.save(fout, self.background)

        b = zlib.compress(fout.getvalue())
        return {'background': b}

    def deserialize(self, data):
        b = data['background']
        fin = cStringIO.StringIO(zlib.decompress(b))
        self.background = np.load(fin)

    def _count(self, gene_syms):
        res = self.cache_get(gene_syms)
        if not res:
            vpred = np.vectorize(lambda sym: sym in gene_syms)
            index = vpred(self.background['sym'])
            res = np.sum(self.background['raw'][index])
            self.cache_store(gene_syms, res)
        return res

    @property
    def _total(self):
        return np.sum(self.background['raw'])


def poisson_test(observed, expected):
    return 1.0


class SamochaBackground(Background, Precompute):
    FILENAME = os.path.join(
        settings.BASE_DIR,
        '..',
        'data/enrichment/background-samocha-et-al.csv')

    def _load_and_prepare_build(self):
        df = pd.read_csv(self.FILENAME)
        return df

    def __init__(self):
        super(SamochaBackground, self).__init__()
        self.name = 'samochaBackgroundModel'
        self.background = self._load_and_prepare_build()

    def precompute(self):
        self.background = self._load_and_prepare_build()
        return self.background

    def serialize(self):
        return {'background': ''}

    def deserialize(self, data):
        self.background = self._load_and_prepare_build()

    def test(self, O, N, effect_type, gene_syms, boys, girls):
        eff = 'P_{}'.format(effect_type.upper())
        assert eff in self.background.columns

        gs = [g.upper() for g in gene_syms]
        df = self.background[self.background['gene'].isin(gs)]
        p_boys = (df['M'] * df[eff]).sum()
        boys_expected = p_boys * boys

        p_girls = (df['F'] * df[eff]).sum()
        girls_expected = p_girls * girls

        expected = boys_expected + girls_expected
        bg_prob = (p_boys + p_girls) / 2.0
        print("observed: {}; trails: {}; expected: {}; bg_prob: {}"
              .format(O, N, expected, bg_prob))
        # p_val = poisson_test(O, expected)
        p_val = stats.binom_test(O, N, p=bg_prob)

        return expected, p_val
