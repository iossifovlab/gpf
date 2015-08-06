'''
Created on Jul 16, 2015

@author: lubo
'''
import numpy as np
from DAE import vDB
import tables
import copy
import operator


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
GENDER_TYPES = tables.Enum(['M', 'F'])
PARENT_TYPES = tables.Enum(['mom', 'dad'])
CHILD_TYPES = tables.Enum(['prb', 'sib'])


class TransmissionQuery(object):
    filters = tables.Filters(complevel=1)
    keys = {'variant_types': list,
            'effect_types': list,
            'gene_syms': list,
            'ultra_rare_only': bool,
            'min_parents_called': int,
            'max_alt_freq_prcnt': float,
            'min_alt_freq_prcnt': float,
            'region': str,
            'family_ids': list,
            'present_in_parent': list,
            'present_in_child': list,
            }

    default_query = {'variant_types': None,
                     'effect_types': None,
                     'gene_syms': None,
                     'ultra_rare_only': False,
                     'min_parents_called': 600,
                     'max_alt_freq_prcnt': 5.0,
                     'min_alt_freq_prcnt': None,
                     'region': None,
                     'family_ids': None,
                     'present_in_parent': None,
                     'present_in_child': None,
                     }

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
        etable = self.hdf5_fh.root.variants.effect
        vtable = self.hdf5_fh.root.variants.summary

        where = self.build_effect_query_where()
        where = where.strip()
        eres = etable.read_where(where)
        vrow = np.unique(eres['vrow'])
        return vtable[vrow]

    def build_effect_query_where(self):
        assert self['effect_types'] or self['gene_syms']

        where = []
        if self['gene_syms']:
            where.append(self.build_gene_syms_where())
        if self['effect_types']:
            where.append(self.build_effect_types_where())
        if self['variant_types']:
            where.append(self.build_variant_types_where())

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

    def build_gene_syms_where(self):
        assert self['gene_syms']
        assert isinstance(self['gene_syms'], list)

        symbols = map(lambda sym: ' ( symbol == "{}" ) '.format(sym),
                      self['gene_syms'])
        where = ' | '.join(symbols)
        return where

    def build_effect_types_where(self):
        assert self['effect_types']
        assert isinstance(self['effect_types'], list)
        assert reduce(operator.and_,
                      map(lambda et: et in EFFECT_TYPES, self['effect_types']))
        where = map(lambda et: ' ( effect_type == {} ) '.format(
            EFFECT_TYPES[et]), self['effect_types'])
        where = ' | '.join(where)
        return where

    def build_variant_types_where(self):
        assert self['variant_types']
        assert isinstance(self['variant_types'], list)
        assert reduce(operator.and_,
                      map(lambda et: et in VARIANT_TYPES,
                          self['variant_types']))
        where = map(lambda et: ' ( variant_type == {} ) '.format(
            VARIANT_TYPES[et]), self['variant_types'])
        where = ' | '.join(where)
        return where

    def build_family_ids_where(self):
        assert self['family_ids']
        assert isinstance(self['family_ids'], list)
        where = map(lambda fid: ' ( family_id == "{}" ) '.format(fid),
                    self['family_ids'])
        where = ' | '.join(where)
        return where

    def build_present_in_parent_where(self):
        assert self['present_in_parent']
        assert isinstance(self['present_in_parent'], list)
        assert reduce(operator.and_,
                      map(lambda p: p in PARENT_TYPES,
                          self['present_in_parent']))
        where = map(lambda p: ' ( in_{} == 1 ) '.format(p),
                    self['present_in_parent'])
        where = ' & '.join(where)
        return where

    def build_present_in_child_where(self):
        assert self['present_in_child']
        assert isinstance(self['present_in_child'], list)
        assert reduce(operator.and_,
                      map(lambda ch: ch in CHILD_TYPES,
                          self['present_in_child']))
        where = map(lambda p: ' ( in_{} == 1 ) '.format(p),
                    self['present_in_child'])
        where = ' & '.join(where)
        return where

    def execute_family_query(self):
        ftable = self.hdf5_fh.root.variants.family
        vtable = self.hdf5_fh.root.variants.summary

        where = self.build_family_query_where()
        where = where.strip()
        frow = ftable.read_where(where)
        # vrow = np.unique(fres['vrow'])
        return vtable[frow]

    def build_family_query_where(self):
        assert self['family_ids'] or self['present_in_parent'] or \
            self['present_in_child']

        where = []
        if self['family_ids']:
            where.append(self.build_family_ids_where())
        if self['present_in_parent']:
            where.append(self.build_present_in_parent_where())
        if self['present_in_child']:
            where.append(self.build_present_in_child_where())

        where.append(self.build_query_alt_freq())

        where = map(lambda s: ' ( {} ) '.format(s), where)
        where = ' & '.join(where)
        return where
