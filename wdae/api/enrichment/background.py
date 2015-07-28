'''
Created on Jun 8, 2015

@author: lubo
'''
import numpy as np
import cStringIO
import zlib

from DAE import vDB
from collections import Counter
import cPickle
from api.precompute.register import Precompute
import csv
import os
from django.conf import settings


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
                effectTypes="synonymous")
    affected_gene_syms = _collect_affected_gene_syms(vs)

    base = [gs for gs in affected_gene_syms if len(gs) == 1]
    foreground = [gs for gs in affected_gene_syms if len(gs) > 1]

    base_counts = _count_gene_syms(base)

    base_sorted = sorted(zip(base_counts.keys(),
                             base_counts.values()))

    b = np.array(base_sorted,
                 dtype=[('sym', '|S32'), ('raw', '>i4')])

    return (b, foreground)


class Background(Precompute):
    def __init__(self):
        self.background = None

    @property
    def is_ready(self):
        return self.background is not None

    def prob(self, gene_syms):
        return 1.0 * self.count(gene_syms) / self.total

    def count(self, gen_syms):
        vpred = np.vectorize(lambda sym: sym in gen_syms)
        index = vpred(self.background['sym'])
        return np.sum(self.background['raw'][index])


class SynonymousBackground(Background):
    TRANSMITTED_STUDY_NAME = 'w1202s766e611'

    def __init__(self):
        super(SynonymousBackground, self).__init__()

    def precompute(self):
        self.background, self.foreground = \
            _build_synonymous_background(self.TRANSMITTED_STUDY_NAME)
        return self.background

    def count_foreground_events(self, gene_syms):
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

    def count(self, gene_syms):
        vpred = np.vectorize(lambda sym: sym in gene_syms)
        index = vpred(self.background['sym'])
        base = np.sum(self.background['raw'][index])
        foreground = self.count_foreground_events(gene_syms)
        return base + foreground

    @property
    def total(self):
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


class CodingLenBackground(Background):
    FILENAME = os.path.join(settings.BASE_DIR,
                            '..',
                            'data/enrichment/background-model-conding-len-in-target.csv')

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

    def precompute(self):
        back = self._load_and_prepare_build()
        self.background = np.array(back,
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

    def count(self, gene_syms):
        vpred = np.vectorize(lambda sym: sym in gene_syms)
        index = vpred(self.background['sym'])
        base = np.sum(self.background['raw'][index])
        return base

    @property
    def total(self):
        return np.sum(self.background['raw'])

