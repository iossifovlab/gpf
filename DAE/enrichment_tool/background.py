'''
Created on Nov 7, 2016

@author: lubo
'''
import cPickle
import cStringIO
from collections import Counter
import csv
import os
from scipy import stats
import zlib

from DAE import vDB, genomesDB
from enrichment_tool.config import BackgroundConfig
import numpy as np
import pandas as pd
from enrichment_tool.event_counters import overlap_enrichment_result_dict


class BackgroundBase(BackgroundConfig):

    def __init__(self, name, use_cache=False):
        super(BackgroundBase, self).__init__()
        self.background = None
        self.name = name
        assert self.name is not None

        if not use_cache:
            self.precompute()
        else:
            if not self.cache_load():
                self.precompute()
                self.cache_save()

    @property
    def cache_filename(self):
        return os.path.join(
            self.cache_dir,
            "{}.pckl".format(self.name))

    def cache_clear(self):
        assert self.name is not None
        if not os.path.exists(self.cache_filename):
            return False
        os.remove(self.cache_filename)
        return True

    def cache_save(self):
        assert self.name is not None
        with open(self.cache_filename, 'w') as output:
            data = self.serialize()
            cPickle.dump(data, output)

    def cache_load(self):
        if not os.path.exists(self.cache_filename):
            return False

        with open(self.cache_filename, 'r') as infile:
            data = cPickle.load(infile)
            self.deserialize(data)

        return True

    @property
    def is_ready(self):
        return self.background is not None


class BackgroundCommon(BackgroundBase):

    def __init__(self, name, use_cache=False):
        super(BackgroundCommon, self).__init__(name, use_cache)

    def _prob(self, gene_syms):
        return 1.0 * self._count(gene_syms) / self._total

    def _calc_enrichment_results_stats(self, background_prob, result):
        events_count = len(result.events)
        result.expected = background_prob * events_count
        result.pvalue = stats.binom_test(
            len(result.overlapped),
            events_count,
            p=background_prob)

    def calc_stats(self, effect_type, enrichment_results,
                   gene_set, children_stats):

        gene_syms = [gs.upper() for gs in gene_set]
        overlap_enrichment_result_dict(enrichment_results, gene_syms)

        background_prob = self._prob(gene_syms)

        self._calc_enrichment_results_stats(
            background_prob, enrichment_results['all'])
        self._calc_enrichment_results_stats(
            background_prob, enrichment_results['rec'])
        self._calc_enrichment_results_stats(
            background_prob, enrichment_results['male'])
        self._calc_enrichment_results_stats(
            background_prob, enrichment_results['female'])

        return enrichment_results


class SynonymousBackground(BackgroundCommon):
    TRANSMITTED_STUDY_NAME = 'w1202s766e611'

    @staticmethod
    def _collect_affected_gene_syms(vs):
        return [set([ge['sym'].upper() for ge in v.requestedGeneEffects])
                for v in vs]

    @staticmethod
    def _collect_unique_gene_syms(affected_gene_sets):
        gene_set = set()
        for gs in affected_gene_sets:
            gene_set |= set(gs)
        return gene_set

    @staticmethod
    def _count_gene_syms(affected_gene_sets):
        background = Counter()
        for gene_set in affected_gene_sets:
            for gene_sym in gene_set:
                background[gene_sym] += 1
        return background

    @staticmethod
    def _build_synonymous_background(transmitted_study_name):
        transmitted_study = vDB.get_study(transmitted_study_name)
        vs = transmitted_study.get_transmitted_summary_variants(
            ultraRareOnly=True,
            minParentsCalled=600,
            effectTypes=["synonymous"])
        affected_gene_syms = \
            SynonymousBackground._collect_affected_gene_syms(vs)

        base = [gs for gs in affected_gene_syms if len(gs) == 1]
        foreground = [gs for gs in affected_gene_syms if len(gs) > 1]

        base_counts = SynonymousBackground._count_gene_syms(base)

        base_sorted = sorted(zip(base_counts.keys(),
                                 base_counts.values()))

        background = np.array(base_sorted,
                              dtype=[('sym', '|S32'), ('raw', '>i4')])

        return (background, foreground)

    def __init__(self, use_cache=False):
        super(SynonymousBackground, self).__init__(
            'synonymousBackgroundModel', use_cache)

    def precompute(self):
        self.background, self.foreground = \
            self._build_synonymous_background(self.TRANSMITTED_STUDY_NAME)
        return self.background

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
        vpred = np.vectorize(lambda sym: sym in gene_syms)
        index = vpred(self.background['sym'])
        base = np.sum(self.background['raw'][index])
        foreground = self._count_foreground_events(gene_syms)
        res = base + foreground
        return res

    @property
    def _total(self):
        return np.sum(self.background['raw']) + len(self.foreground)


class CodingLenBackground(BackgroundCommon):

    @property
    def filename(self):
        return self[self.name, 'file']

    def _load_and_prepare_build(self):
        filename = self.filename
        assert filename is not None
        back = []
        with open(filename, 'r') as f:
            reader = csv.reader(f)
            reader.next()
            for row in reader:
                back.append((str(row[1]), int(row[2])))
        return back

    def __init__(self, use_cache=False):
        super(CodingLenBackground, self).__init__(
            'codingLenBackgroundModel', use_cache)

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
        vpred = np.vectorize(lambda sym: sym in gene_syms)
        index = vpred(self.background['sym'])
        res = np.sum(self.background['raw'][index])
        return res

    @property
    def _total(self):
        return np.sum(self.background['raw'])


def poisson_test(observed, expected):
    # Bernard Rosner, Fundamentals of Biostatistics, 8th edition,
    # pp 260-261
    rv = stats.poisson(expected)
    if observed >= expected:
        p = rv.cdf(observed - 1)
        p_value = 2 * (1 - p)
    else:
        p = rv.cdf(observed)
        p_value = 2 * p

    return min(p_value, 1)


class SamochaBackground(BackgroundBase):

    def _load_and_prepare_gender_count(self, df):
        GM = genomesDB.get_gene_models()  # @UndefinedVariable

        df['F'] = pd.Series(2, index=df.index)
        df['M'] = pd.Series(2, index=df.index)

        for gene_name in df['gene']:
            gene_loc = df['gene'] == gene_name
            gms = GM.gene_models_by_gene_name(gene_name)
            chromes = []
            for tm in gms:
                chromes.append(tm.chr)
            if 'X' in chromes:
                df.loc[gene_loc, 'F'] = 2
                df.loc[gene_loc, 'M'] = 1
            elif 'Y' in chromes:
                df.loc[gene_loc, 'F'] = 0
                df.loc[gene_loc, 'M'] = 1
        return df

    def _load_and_prepare_probabilities(self, df):
        df.fillna(-99, inplace=True)
        df['P_LGDS'] = pd.Series(1E-99, index=df.index)
        df['P_MISSENSE'] = pd.Series(1E-99, index=df.index)
        df['P_SYNONYMOUS'] = pd.Series(1E-99, index=df.index)

        df['P_LGDS'] = np.power(10, df['nonsense'].values) + \
            np.power(10.0, df['splice-site'].values) + \
            np.power(10.0, df['frame-shift'].values)
        df['P_MISSENSE'] = np.power(10, df['missense'].values)
        df['P_SYNONYMOUS'] = np.power(10, df['synonymous'].values)

        return df

    def _load_and_prepare_gene_upper(self, df):
        df['gene'] = df['gene'].str.upper()
        return df

    @property
    def filename(self):
        return self[self.name, 'file']

    def _load_and_prepare_build(self):
        filename = self.filename
        assert filename is not None

        df = pd.read_csv(filename)
        # df = self._load_and_prepare_gender_count(df)
        # df = self._load_and_prepare_probabilities(df)
        # df = self._load_and_prepare_gene_upper(df)

        return df

    def __init__(self, use_cache=False):
        super(SamochaBackground, self).__init__(
            'samochaBackgroundModel', use_cache)

    def precompute(self):
        self.background = self._load_and_prepare_build()
        return self.background

    def serialize(self):
        ndarray = self.background.as_matrix(
            ['gene', 'F', 'M', 'P_LGDS', 'P_MISSENSE', 'P_SYNONYMOUS'])
        fout = cStringIO.StringIO()
        np.save(fout, ndarray)

        data = zlib.compress(fout.getvalue())
        return {'background': data}

    def deserialize(self, data):
        b = data['background']
        fin = cStringIO.StringIO(zlib.decompress(b))
        ndarray = np.load(fin)

        self.background = pd.DataFrame(
            ndarray,
            columns=['gene', 'F', 'M', 'P_LGDS', 'P_MISSENSE', 'P_SYNONYMOUS'])

    def calc_stats(self, effect_type, enrichment_results,
                   gene_set, children_stats):

        overlap_enrichment_result_dict(enrichment_results, gene_set)

        eff = 'P_{}'.format(effect_type.upper())
        assert eff in self.background.columns

        all_result = enrichment_results['all']
        male_result = enrichment_results['male']
        female_result = enrichment_results['female']
        rec_result = enrichment_results['rec']

        gs = [g.upper() for g in gene_set]
        df = self.background[self.background['gene'].isin(gs)]
        p_boys = (df['M'] * df[eff]).sum()
        # result.male_expected = p_boys * events.male_count
        male_result.expected = p_boys * children_stats['M']

        p_girls = (df['F'] * df[eff]).sum()
        # result.female_expected = p_girls * events.female_count
        female_result.expected = p_boys * children_stats['F']

        all_result.expected = male_result.expected + female_result.expected

        all_result.pvalue = poisson_test(
            len(all_result.overlapped),
            all_result.expected)
        male_result.pvalue = poisson_test(
            len(male_result.overlapped),
            male_result.expected)
        female_result.pvalue = poisson_test(
            len(female_result.overlapped),
            female_result.expected)

        # p = (p_boys + p_girls) / 2.0
        p = (children_stats['M'] * p_boys + children_stats['F'] * p_girls) / \
            (children_stats['M'] + children_stats['F'])
#         result.rec_expected = \
#             (children_stats['M'] + children_stats['F']) * p * p
        rec_result.expected = (children_stats['M'] + children_stats['F']) * \
            p * len(rec_result.events) / len(all_result.events)

        rec_result.pvalue = poisson_test(
            len(rec_result.overlapped),
            rec_result.expected)

        return enrichment_results
