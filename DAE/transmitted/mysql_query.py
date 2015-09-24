'''
Created on Sep 24, 2015

@author: lubo
'''
import MySQLdb as mdb
import copy


class MysqlTransmittedQuery(object):
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

    def execute(self):
        cursor = self.connection.cursor(mdb.cursors.DictCursor)
        cursor.execute(self.query)
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

    def get_transmitted_summary_variants(self, **kwargs):
        pass
