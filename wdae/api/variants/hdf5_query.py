'''
Created on Jul 16, 2015

@author: lubo
'''
import numpy as np
from api.variants.transmitted_variants import parse_family_data
from DAE import vDB
import gzip
from VariantsDB import parseGeneEffect
import itertools
import tables
import copy


EFFECT_TYPES = tables.Enum([
        "3'UTR",
        "3'UTR-intron",
        "5'UTR",
        "5'UTR-intron",
        'frame-shift',
        'intergenic',
        'intron',
        'missense',
        'no-frame-shift',
        'no-frame-shift-newStop',
        'noEnd',
        'noStart',
        'non-coding',
        'non-coding-intron',
        'nonsense',
        'splice-site',
        'synonymous'])

VARIANT_TYPES = tables.Enum(['del', 'ins', 'sub', 'CNV'])


class SummaryVariants(tables.IsDescription):
    line_number = tables.Int64Col()

    chrome = tables.StringCol(3)
    position = tables.Int64Col()
    variant = tables.StringCol(45)
    variant_type = tables.EnumCol(VARIANT_TYPES,
                                  'sub', base='uint8')
    effect_type = tables.EnumCol(EFFECT_TYPES,
                                 'intergenic', base='uint8')
    effect_gene = tables.StringCol(32)

    fbegin = tables.Int64Col()
    fend = tables.Int64Col()
    ebegin = tables.Int64Col()
    eend = tables.Int64Col()
    elen = tables.Int32Col()

    n_par_called = tables.Int16Col()  # 'all.nParCalled'
    n_alt_alls = tables.Int16Col()  # 'all.nAltAlls'
    alt_freq = tables.Float16Col()  # 'all.altFreq'

    prcnt_par_called = tables.Float16Col()  # 'all.prcntParCalled'
    seg_dups = tables.Int16Col()  # 'segDups
    hw = tables.Float16Col()  # 'HW'
    ssc_freq = tables.Float16Col()  # 'SSC-freq'
    evs_freq = tables.Float16Col()  # 'EVS-freq'
    e65_freq = tables.Float16Col()  # 'E65-freq'


class FamilyVariants(tables.IsDescription):
    fid = tables.StringCol(16)
    best = tables.StringCol(16)
    counts = tables.StringCol(64)
    vrow = tables.Int64Col()


class GeneEffectVariants(tables.IsDescription):
    symbol = tables.StringCol(32)
    effect = tables.EnumCol(EFFECT_TYPES,
                            'intergenic', base='uint8')
    vrow = tables.Int64Col()

    n_par_called = tables.Int16Col()  # 'all.nParCalled'
    n_alt_alls = tables.Int16Col()  # 'all.nAltAlls'
    alt_freq = tables.Float16Col()  # 'all.altFreq'


class TransmissionQuery(object):
    filters = tables.Filters(complevel=1)
    keys = {'variant_types': list,
            'effect_types': list,
            'gene_syms': list,
            'ultra_rare_only': bool,
            'min_parents_called': int,
            'max_alt_freq_prcnt': float,
            'min_alt_freq_prcnt': float,
            'region': str}

    default_query = {'variant_types': None,
                     'effect_types': None,
                     'gene_syms': None,
                     'ultra_rare_only': False,
                     'min_parents_called': 600,
                     'max_alt_freq_prcnt': 5.0,
                     'min_alt_freq_prcnt': None,
                     'region': None}

    def __init__(self, study_name):
        self.study_name = study_name
        self.hdf5_filename = vDB._config.get(
                    'study.' + self.study_name,
                    'transmittedVariants.hdf5')
        self.hdf5_fh = tables.open_file(self.hdf5_filename, "r",
                                        filters=self.filters)

        self.query = copy.deepcopy(self.default_query)

        self.ewhere = []

    def __getitem__(self, key):
        if key not in self.keys:
            raise KeyError('unexpected key: {}'.format(key))
        return self.query.get(key, None)

    def __setitem__(self, key, value):
        if key not in self.keys:
            raise KeyError('unexpected key: {}'.format(key))
        self.query[key] = value

    def clear_query(self):
        self.ewhere = []
        self.query = copy.deepcopy(self.default_query)

    def execute_effect_query(self):
        etable = self.hdf5_fh.root.effect.effect
        vtable = self.hdf5_fh.root.summary.variants

        where = self.build_effect_query_where()
        where = where.strip()
        eres = etable.read_where(where)
        vrow = np.unique(eres['vrow'])
        return vtable[vrow]

    def build_effect_query_where(self):
        where = []
        where.append(self.build_query_by_gene_syms())
        where.append(self.build_query_alt_freq())

        where = map(lambda s: ' ( {} ) '.format(s), where)
        where = ' & '.join(where)
        return where

    def build_query_alt_freq(self):
        where = []
        if self['min_parents_called']:
            where.append(
                ' ( n_par_called > {} ) '.format(self['min_parents_called']))
        if self['ultra_rare_only']:
            where.append(' ( n_alt_alls == 1 ) ')
        else:
            if self['max_alt_freq_prcnt']:
                where.append(
                    ' ( alt_freq <= {} ) '.format(self['max_alt_freq_prcnt']))
            if self['min_alt_freq_prcnt']:
                where.append(
                    ' ( alt_freq >= {} ) '.format(self['min_alt_freq_prcnt']))

        res = ' & '.join(where)
        return res

    def build_query_by_gene_syms(self):
        assert self['gene_syms']
        assert isinstance(self['gene_syms'], list)
        assert len(self['gene_syms']) > 0
        symbols = map(lambda sym: ' ( symbol == "{}" ) '.format(sym),
                      self['gene_syms'])
        where = ' | '.join(symbols)
        return where
