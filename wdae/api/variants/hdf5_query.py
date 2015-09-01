'''
Created on Jul 16, 2015

@author: lubo
'''
import numpy as np
import tables
import copy
import operator
from DAE import vDB


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
            'present_in_child_gender': list,
            'regions': list,
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
                     'present_in_child_gender': None,
                     'regions': None,
                     }

    def __init__(self, study_name):
        self.study_name = study_name
        self.hdf5_filename = vDB._config.get(
                    'study.' + self.study_name,
                    'transmittedVariants.hdf5')
        # self.hdf5_filename = '{}.hdf5'.format(study_name)
        self.hdf5_fh = tables.open_file(self.hdf5_filename, "r",
                                        filters=self.filters)

        self.query = copy.deepcopy(self.default_query)

    def __getitem__(self, key):
        if key not in self.keys:
            raise KeyError('unexpected key: {}'.format(key))
        return self.query.get(key, None)

    def __setitem__(self, key, value):
        if key not in self.keys:
            raise KeyError('unexpected key: {}'.format(key))
        self.query[key] = value

    def clear_query(self):
        self.query = copy.deepcopy(self.default_query)

    def execute_effect_query(self):
        etable = self.hdf5_fh.root.variants.effect
        vtable = self.hdf5_fh.root.variants.summary

        where = self.build_effect_query_where()
        where = where.strip()
        print "EFFECT:", where
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

        freq_where = self.build_freq_where()
        if freq_where:
            where.append(freq_where)

        where = map(lambda s: ' ( {} ) '.format(s), where)
        where = ' & '.join(where)
        return where

    def build_freq_where(self):
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

    def build_present_in_child_gender_where(self):
        assert self['present_in_child_gender']
        assert isinstance(self['present_in_child_gender'], list)
        assert reduce(operator.and_,
                      map(lambda g: g in GENDER_TYPES,
                          self['present_in_child_gender']))
        where = []
        if 'M' in self['present_in_child_gender']:
            where.append(
                ' ( in_prb_gender == {} ) | ( in_sib_gender == {} ) '
                .format(GENDER_TYPES['M'], GENDER_TYPES['M']))
        if 'F' in self['present_in_child_gender']:
            where.append(
                ' ( in_prb_gender == {} ) | ( in_sib_gender == {} ) '
                .format(GENDER_TYPES['F'], GENDER_TYPES['F']))
        if len(where) == 2:
            where = None
        else:
            where = where[0]
        return where

    def execute_family_query(self):
        ftable = self.hdf5_fh.root.variants.family
        # vtable = self.hdf5_fh.root.variants.summary

        where = self.build_family_query_where()
        where = where.strip()
        frow = ftable.read_where(where)
        # vrow = np.unique(fres['vrow'])
        return frow

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
        if self['present_in_child_gender']:
            clause = self.build_present_in_child_gender_where()
            if clause:
                where.append(clause)

        # where.append(self.build_freq_where())

        where = map(lambda s: ' ( {} ) '.format(s), where)
        where = ' & '.join(where)
        return where

    def is_family_query(self):
        if self['family_ids']:
            return True
        return False

    def is_effect_query(self):
        if self['gene_syms'] or self['effect_types']:
            return True
        return False

    def get_summary_variants(self):
        vrows = []
        if self.is_family_query():
            raise NotImplemented('query by family ids not implemented yet')
        elif self.is_effect_query():
            pass
        else:  # summary query
            vrows = self.execute_summary_variants_query()
        return vrows

    def build_regions_where(self):
        assert self['regions']
        assert isinstance(self['regions'], list)

        def region_where(chrome, beg, end):
            p = '((chrome == "{}") & (position >= {}) & (position <= {}))'
            return p.format(chrome, beg, end)

        regions = self['regions']
        where = []
        for r in regions:
            col_pos = r.find(":")
            chrome = r[0:col_pos]

            dash_pos = r.find("-")
            beg = int(r[col_pos + 1:dash_pos])
            end = int(r[dash_pos + 1:])

            where.append(region_where(chrome, beg, end))

        return ' | '.join(where)

    def build_summary_query_where(self):
        where = []
        if self['regions']:
            where.append(self.build_regions_where())

        where.append(self.build_freq_where())

        where = map(lambda s: ' ( {} ) '.format(s), where)
        where = ' & '.join(where)
        return where

    def execute_summary_variants_query(self):
        vtable = self.hdf5_fh.root.variants.summary

        where = self.build_summary_query_where()
        where = where.strip()
        vrow = vtable.read_where(where)
        return vrow

    def get_variants(self):
        vrows = self.execute_effect_query()
        ftable = self.hdf5_fh.root.variants.family
        res = []
        for v in vrows:
            frows = ftable[v['fbegin']:v['fend']]
            vf = np.vectorize(lambda f: f)
            idx = np.apply_along_axis(vf, 0, frows['in_prb'])
            res.append(frows[idx])
            # res.append(frows)
        return np.concatenate(res, axis=0)
        # return itertools.chain(*res)
