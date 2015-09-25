'''
Created on Sep 24, 2015

@author: lubo
'''
import MySQLdb as mdb
import copy
import operator


class MysqlTransmittedQuery(object):
    EFFECT_TYPES = [
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
        'synonymous']

    keys = {'variantTypes': list,
            'effectTypes': list,
            'geneSyms': list,
            'ultraRareOnly': bool,
            'minParentsCalled': int,
            'maxAltFreqPrcnt': float,
            'minAltFreqPrcnt': float,
            'family_ids': list,
            'present_in_parent': list,
            'present_in_child': list,
            'present_in_child_gender': list,
            'regionS': list,
            }

    default_query = {'variantTypes': None,
                     'effectTypes': None,
                     'geneSyms': None,
                     'ultraRareOnly': False,
                     'minParentsCalled': 600,
                     'maxAltFreqPrcnt': 5.0,
                     'minAltFreqPrcnt': None,
                     'family_ids': None,
                     'present_in_parent': None,
                     'present_in_child': None,
                     'present_in_child_gender': None,
                     'regionS': None,
                     }

    def _get_config_property(self, name):
        return self.vdb._config.get(self.config_section, name)

    def __init__(self, vdb, study_name):
        self.study_name = study_name
        self.vdb = vdb
        self.config_section = 'study.' + study_name
        self.db = self._get_config_property('transmittedVariants.mysql.db')
        self.user = self._get_config_property('transmittedVariants.mysql.user')
        self.passwd = \
            self._get_config_property('transmittedVariants.mysql.pass')
        assert self.db
        assert self.user
        assert self.passwd
        self.connection = None
        self.query = copy.deepcopy(self.default_query)

    def connect(self):
        assert not self.connection

        self.connection = mdb.connect('127.0.0.1',
                                      self.user,
                                      self.passwd,
                                      self.db)

    def execute(self, select):
        cursor = self.connection.cursor(mdb.cursors.DictCursor)
        cursor.execute(select)
        return cursor.fetchall()

    def disconnect(self):
        if not self.connection:
            return
        self.connection.close()
        self.connection = None

    def __getitem__(self, key):
        if key not in self.keys:
            raise KeyError('unexpected key: {}'.format(key))
        return self.query.get(key, None)

    def _build_freq_where(self):
        where = []
        if self['minParentsCalled']:
            where.append(
                ' ( tsv.n_par_called > {} ) '.format(
                    self['minParentsCalled']))
        if self['ultraRareOnly']:
            where.append(' ( tsv.n_alt_alls == 1 ) ')
        else:
            if self['maxAltFreqPrcnt']:
                where.append(
                    ' ( tsv.alt_freq <= {} ) '.format(self['maxAltFreqPrcnt']))
            if self['minAltFreqPrcnt']:
                where.append(
                    ' ( tsv.alt_freq >= {} ) '.format(self['minAltFreqPrcnt']))

        res = ' AND '.join(where)
        return res

    def _build_effect_type_where(self):
        assert self['effectTypes']
        assert isinstance(self['effectTypes'], list)
        assert reduce(operator.and_,
                      map(lambda et: et in self.EFFECT_TYPES,
                          self['effectTypes']))
        where = map(lambda ef: " '{}' ".format(ef), self['effectTypes'])
        where = ' tge.effect_type in ( {} ) '.format(','.join(where))
        return where

    def _build_gene_syms_where(self):
        assert self['geneSyms']
        assert isinstance(self['geneSyms'], list)
        where = map(lambda sym: " '{}' ".format(sym), self['geneSyms'])
        where = ' tge.symbol in ( {} ) '.format(','.join(where))
        return where

    def _build_where(self, kwargs):
        where = []
        if 'effectTypes' in kwargs:
            self.query['effectTypes'] = kwargs['effectTypes']
            where.append(self._build_effect_type_where())

        if 'geneSyms' in kwargs:
            self.query['geneSyms'] = kwargs['geneSyms']
            where.append(self._build_gene_syms_where())

        where.append(self._build_freq_where())
        w = ' AND '.join(where)
        return w

#     def get_transmitted_summary_variants(self, **kwargs):
#         where = self._build_where(kwargs)
#
#         select = 'select id ' \
#             'from transmitted_summaryvariant as tsv where {}'.format(where)
#         # print(select)
#         return self.execute(select)

    def get_transmitted_summary_variants(self, **kwargs):
        where = self._build_where(kwargs)
        select = \
            "select distinct tsv.id " \
            "from transmitted_summaryvariant as tsv " \
            "left join transmitted_geneeffectvariant as tge " \
            "on tsv.id = tge.summary_variant_id " \
            "where {} " \
            "group by tsv.id".format(where)
        # print(select)
        return self.execute(select)
