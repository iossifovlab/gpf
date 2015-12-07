'''
Created on Sep 24, 2015

@author: lubo
'''
import MySQLdb as mdb
# import pymysql as mdb
import copy
import operator
import re
from Variant import Variant, parseGeneEffect, filter_gene_effect
from transmitted.base_query import TransmissionConfig
import logging


LOGGER = logging.getLogger(__name__)


class MysqlTransmittedQuery(TransmissionConfig):
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
        'synonymous',
        'CDS',
        'CNV+',
        'CNV-', ]

    VARIANT_TYPES = [
        'del', 'ins', 'sub', 'CNV']

    PRESENT_IN_PARENT_TYPES = [
        "mother only", "father only",
        "mother and father", "neither",
    ]

    PRESENT_IN_CHILD_TYPES = [
        "autism only",
        "unaffected only",
        "autism and unaffected",
        "proband only",
        "sibling only",
        "proband and sibling",
        "neither",
    ]

    IN_CHILD_TYPES = [
        'prb',
        'sib',
        'prbM',
        'prbF',
        'sibM',
        'sibF',
    ]

    KEYS = {
        'variantTypes': list,
        'effectTypes': list,
        'geneSyms': list,
        'geneSymsUpper': list,
        'ultraRareOnly': bool,
        'minParentsCalled': int,
        'maxAltFreqPrcnt': float,
        'minAltFreqPrcnt': float,
        'presentInParent': list,
        'inChild': str,
        'presentInChild': list,
        'gender': list,
        'regionS': list,
        'familyIds': list,
        'TMM_ALL': bool,
        'limit': int,
    }

    DEFAULT_QUERY = {
        'variantTypes': None,
        'effectTypes': None,
        'geneSyms': None,
        'geneSymsUpper': None,
        'ultraRareOnly': False,
        'minParentsCalled': 0,
        'maxAltFreqPrcnt': 5.0,
        'minAltFreqPrcnt': None,
        'presentInParent': None,
        'inChild': None,
        'presentInChild': None,
        'gender': None,
        'regionS': None,
        'familyIds': None,
        'TMM_ALL': False,
        'limit': None,
    }

    def _get_config_property(self, name):
        return self.vdb._config.get(self.config_section, name)

    def __init__(self, study, call_set=None):
        super(MysqlTransmittedQuery, self).__init__(study, call_set)
        assert self._get_params("format") == 'mysql'

        self.study = study
        self.db = self._get_params('db')
        self.user = self._get_params('user')
        self.passwd = self._get_params('pass')
        self.host = self._get_params("host")

        assert self.host
        assert self.db
        assert self.user
        assert self.passwd

        self.connection = None
        self.query = copy.deepcopy(self.DEFAULT_QUERY)
        self.connect()

    def connect(self):
        if not self.connection:
            LOGGER.info("creating new mysql connection")
            self.connection = mdb.connect(self.host,
                                          self.user,
                                          self.passwd,
                                          self.db)
        return self.connection

    def execute(self, select):
        #         if not self.connection:
        #             self.connect()
        LOGGER.info("creating new mysql connection")
        connection = mdb.connect(self.host,
                                 self.user,
                                 self.passwd,
                                 self.db)

        cursor = connection.cursor(mdb.cursors.DictCursor)
        cursor.execute(select)
        return (connection, cursor)

    def disconnect(self):
        LOGGER.info("closing mysql connection")
        if not self.connection:
            return
        self.connection.close()
        self.connection = None

    def __getitem__(self, key):
        if key not in self.KEYS:
            raise KeyError('unexpected key: {}'.format(key))
        return self.query.get(key, None)

    def _build_freq_where(self):
        where = []
        if self['minParentsCalled']:
            where.append(
                ' ( tsv.n_par_called > {} ) '.format(
                    self['minParentsCalled']))
        if self['ultraRareOnly']:
            where.append(' ( tsv.n_alt_alls = 1 ) ')
        else:
            if self['maxAltFreqPrcnt']:
                where.append(
                    ' ( tsv.alt_freq <= {} ) '.format(self['maxAltFreqPrcnt']))
            if self['minAltFreqPrcnt']:
                where.append(
                    ' ( tsv.alt_freq >= {} ) '.format(self['minAltFreqPrcnt']))

        res = ' AND '.join(where)
        return res

    def _build_family_ids_where(self):
        assert self['familyIds']
        assert isinstance(self['familyIds'], list)

        where = map(lambda fid: " '{}' ".format(fid), self['familyIds'])
        where = ' tfv.family_id in ( {} ) '.format(','.join(where))
        return where

    def _build_variant_type_where(self):
        assert self['variantTypes']
        assert isinstance(self['variantTypes'], list)
        assert reduce(operator.and_,
                      map(lambda et: et in self.VARIANT_TYPES,
                          self['variantTypes']))
        if len(set(self['variantTypes'])) == 4:
            return None
        where = map(lambda ef: " '{}' ".format(ef), self['variantTypes'])
        where = ' tsv.variant_type in ( {} ) '.format(','.join(where))
        return where

    def _build_gene_syms_where(self):
        assert self['geneSyms']
        assert isinstance(self['geneSyms'], list) or \
            isinstance(self['geneSyms'], set)
        self.query['geneSymsUpper'] = [sym.upper() for sym in self['geneSyms']]
        where = map(lambda sym: ' "{}" '.format(sym), self['geneSymsUpper'])
        where = ' tge.symbol in ( {} ) '.format(','.join(where))
        return where

    def _build_effect_type_where(self):
        assert self['effectTypes']
        assert isinstance(self['effectTypes'], list)
        assert reduce(operator.and_,
                      map(lambda et: et in self.EFFECT_TYPES,
                          self['effectTypes']))
        where = map(lambda ef: ' "{}" '.format(ef), self['effectTypes'])
        where = ' tge.effect_type in ( {} ) '.format(','.join(where))
        return where

    def _build_effect_where(self):
        assert self['effectTypes'] or self['geneSyms']
        where = []
        if self['effectTypes']:
            # self.query['effectTypes'] = kwargs['effectTypes']
            where.append(self._build_effect_type_where())

        if self['geneSyms']:
            # self.query['geneSyms'] = kwargs['geneSyms']
            where.append(self._build_gene_syms_where())

        w = ' AND '.join(where)
        return w

    REGION_REGEXP = re.compile("([1-9,X][0-9]?):(\d+)-(\d+)")

    def _build_region_where(self, region):
        m = self.REGION_REGEXP.match(region)
        if not m:
            return None

        res = m.group(1), int(m.group(2)), int(m.group(3))
        return " ( tsv.chrome = '{}' AND " \
            "tsv.position > {} AND " \
            "tsv.position < {} ) ".format(*res)

    def _build_regions_where(self):
        assert self['regionS']
        assert isinstance(self['regionS'], list)
        where = [self._build_region_where(region)
                 for region in self['regionS']]
        where = [w for w in where if w]

        if not where:
            return None
        where = " ( {} ) ".format(" OR ".join(where))
        return where

    PRESENT_IN_PARENT_MAPPING = {
        "mother only": " ( tfv.in_mom = 1  and tfv.in_dad = 0 ) ",
        "father only": " ( tfv.in_dad = 1  and tfv.in_mom = 0 ) ",
        "mother and father": " ( tfv.in_mom = 1 and tfv.in_dad = 1 ) ",
        "neither": " ( tfv.in_mom = 0 and tfv.in_dad = 0 ) ",
    }

    def _build_present_in_parent_where(self):
        assert self['presentInParent']
        assert isinstance(self['presentInParent'], list)
        assert reduce(operator.and_,
                      map(lambda p: p in self.PRESENT_IN_PARENT_TYPES,
                          self['presentInParent']))
        w = [self.PRESENT_IN_PARENT_MAPPING[pip]
             for pip in self['presentInParent']]
        # print("PRESENT_IN_PARENT: {}".format(w))
        if len(set(w)) == 4:
            # print("PRESENT_IN_PARENT: {}".format(set(w)))
            return None

        where = " ( {} ) ".format(' OR '.join(w))
        return where

    PRESENT_IN_CHILD_MAPPING = {
        "autism only": " ( tfv.in_prb = 1 and tfv.in_sib = 0 ) ",
        "unaffected only": " ( tfv.in_sib = 1 and tfv.in_prb = 0 ) ",
        "autism and unaffected": " ( tfv.in_prb = 1 and tfv.in_sib = 1 ) ",
        "proband only": " ( tfv.in_prb = 1 and tfv.in_sib = 0 ) ",
        "sibling only": " ( tfv.in_sib = 1 and tfv.in_prb = 0 ) ",
        "proband and sibling": " ( tfv.in_prb = 1 and tfv.in_sib = 1 ) ",
        "neither": " ( tfv.in_prb = 0 and tfv.in_sib = 0 ) ",
        ("autism only", 'F'):
            " ( tfv.in_prb = 1 and tfv.in_sib = 0 and "
            " tfv.in_prb_gender = 'F' ) ",
        ("autism only", 'M'):
            " ( tfv.in_prb = 1 and tfv.in_sib = 0 and "
            " tfv.in_prb_gender = 'M' ) ",
        ("unaffected only", 'F'):
            " ( tfv.in_sib = 1 and tfv.in_prb = 0 and "
            " tfv.in_sib_gender = 'F' ) ",
        ("unaffected only", 'M'):
            " ( tfv.in_sib = 1 and tfv.in_prb = 0 and "
            " tfv.in_sib_gender = 'M' ) ",
        ("autism and unaffected", 'F'):
            " ( tfv.in_prb = 1 and tfv.in_sib = 1 and "
            " ( tfv.in_prb_gender = 'F' or tfv.in_sib_gender = 'F' ) ) ",
        ("autism and unaffected", 'M'):
            " ( tfv.in_prb = 1 and tfv.in_sib = 1 and "
            " ( tfv.in_prb_gender = 'M' or tfv.in_sib_gender = 'M' ) ) ",
        ("neither", 'F'):
            " ( tfv.in_prb = 0 and tfv.in_sib = 0 and "
            " ( tfv.in_prb_gender = 'F' or tfv.in_sib_gender = 'F' ) ) ",
        ("neither", 'M'):
            " ( tfv.in_prb = 0 and tfv.in_sib = 0 and "
            " ( tfv.in_prb_gender = 'M' or tfv.in_sib_gender = 'M' ) ) ",
    }

    def _build_present_in_child_where(self):
        assert self['presentInChild']
        assert isinstance(self['presentInChild'], list)
        assert reduce(operator.and_,
                      map(lambda p: p in self.PRESENT_IN_CHILD_TYPES,
                          self['presentInChild']))
        if not self['gender'] or set(self['gender']) == set(['M', 'F']):
            w = [self.PRESENT_IN_CHILD_MAPPING[pic]
                 for pic in self['presentInChild']]
        else:
            assert len(self['gender']) == 1
            g = self['gender'][0]
            w = [self.PRESENT_IN_CHILD_MAPPING[(pic, g)]
                 for pic in self['presentInChild']]

        where = " ( {} ) ".format(' OR '.join(w))
        return where

    IN_CHILD_MAPPING = {
        'prb': " ( tfv.in_prb = 1 ) ",
        'sib': " ( tfv.in_sib = 1 ) ",
        'prbM': " ( tfv.in_prb = 1 and tfv.in_prb_gender = 'M' ) ",
        'prbF': " ( tfv.in_prb = 1 and tfv.in_prb_gender = 'F' ) ",
        'sibM': " ( tfv.in_sib = 1 and tfv.in_sib_gender = 'M' ) ",
        'sibF': " ( tfv.in_sib = 1 and tfv.in_sib_gender = 'F' ) ",
    }

    def _build_in_child_where(self):
        assert self['inChild']
        assert isinstance(self['inChild'], str)
        assert self['inChild'] in self.IN_CHILD_TYPES

        where = self.IN_CHILD_MAPPING[self['inChild']]
        return where

    def _build_summary_where(self):
        where = []
        if self['effectTypes'] or self['geneSyms']:
            where.append(self._build_effect_where())
        if self['variantTypes']:
            w = self._build_variant_type_where()
            if w is not None:
                where.append(w)
        if self['regionS']:
            w = self._build_regions_where()
            if w is None:
                print "bad regions: {}".format(self['regionS'])
            else:
                where.append(w)
        fw = self._build_freq_where()
        if fw:
            where.append(self._build_freq_where())
        if not where:
            return ""
        w = ' AND '.join(where)
        summary_where = \
            "tsv.id IN (SELECT distinct tsv.id " \
            "FROM transmitted_summaryvariant AS tsv " \
            "LEFT JOIN transmitted_geneeffectvariant AS tge " \
            "ON tsv.id = tge.summary_variant_id  WHERE {})".format(w)
        return summary_where

    def _build_family_where(self):
        where = []
        if self['familyIds']:
            where.append(self._build_family_ids_where())
        if self['presentInParent']:
            w = self._build_present_in_parent_where()
            if w is not None:
                where.append(w)
        if self['inChild']:
            w = self._build_in_child_where()
            where.append(w)
        elif self['presentInChild']:
            w = self._build_present_in_child_where()
            where.append(w)

        if not where:
            return ""
        w = ' AND '.join(where)
        return w

    def _build_limit(self):
        assert self['limit']
        assert isinstance(self['limit'], int)
        return " LIMIT {}".format(self['limit'])

    def _build_where(self):
        summary_where = self._build_summary_where()
        family_where = self._build_family_where()

        if not family_where:
            w = summary_where
        elif not summary_where:
            w = family_where
        else:
            w = "{} AND {}".format(family_where, summary_where)

        if self['limit']:
            w += self._build_limit()

        return w

    SPECIAL_KEYS = {
        "minParentsCalled": (-1),
        "maxAltFreqPrcnt": (-1),
        "minAltFreqPrcnt": (-1),
    }

    def _copy_kwargs(self, kwargs):
        self.query = copy.deepcopy(self.DEFAULT_QUERY)

        if 'effectTypes' in kwargs and isinstance(kwargs['effectTypes'], str):
            effectTypes = self.study.vdb.effectTypesSet(kwargs['effectTypes'])
            kwargs['effectTypes'] = list(effectTypes)

        for field in kwargs:
            if field in self.KEYS:
                if field not in self.SPECIAL_KEYS:
                    self.query[field] = kwargs[field]
                else:
                    if kwargs[field] == self.SPECIAL_KEYS[field]:
                        self.query[field] = None
                    else:
                        self.query[field] = kwargs[field]

    def _build_variant_pop_type(self, atts, v):
        if atts['all.nAltAlls'] == 1:
            v.popType = "ultraRare"
        else:
            v.popType = "common"  # rethink

    def _build_variant_properties(self, atts):
        v = Variant(atts)
        v.study = self.study

        self._build_variant_pop_type(atts, v)
        self._build_variant_gene_effect(atts, v)

        return v

    def _build_variant_gene_effect(self, atts, v):
        geneEffect = None
        if self['effectTypes'] or self['geneSymsUpper']:
            geneEffect = parseGeneEffect(atts['effectGene'])
            if 'requestedGeneEffects' in atts:
                requestedGeneEffects = parseGeneEffect(
                    atts['requestedGeneEffects'])
            else:
                requestedGeneEffects = filter_gene_effect(
                    geneEffect,
                    self['effectTypes'],
                    self['geneSymsUpper'])
        if geneEffect:
            v._geneEffect = geneEffect
            v._requestedGeneEffect = requestedGeneEffects

    def get_transmitted_summary_variants(self, **kwargs):
        self._copy_kwargs(kwargs)
        where = self._build_where()
        select = \
            "select tsv.id, " \
            "tsv.chrome as chr, " \
            "tsv.position as position, " \
            "tsv.variant as variant, "\
            "tsv.n_par_called as `all.nParCalled`, " \
            "tsv.prcnt_par_called as `all.prcntParCalled`, " \
            "tsv.n_alt_alls as `all.nAltAlls`, " \
            "tsv.alt_freq as `all.altFreq`, " \
            "tsv.effect_type as effectType, " \
            "tsv.effect_gene_all as `effectGene`, " \
            "tsv.effect_details as `effectDetails`, " \
            "tsv.seg_dups as `segDups`, " \
            "tsv.hw as `HW`, " \
            "tsv.ssc_freq as `SSC-freq`, " \
            "tsv.evs_freq as `EVS-freq`, " \
            "tsv.e65_freq as `E65-freq` " \
            "from transmitted_summaryvariant as tsv " \
            "where {}".format(where)

        try:
            connection, cursor = self.execute(select)
            v = cursor.fetchone()

            while v is not None:
                v["location"] = v["chr"] + ":" + str(v["position"])
                vr = self._build_variant_properties(v)

                yield vr
                v = cursor.fetchone()
        except StopIteration:
            connection.close()
        except Exception as ex:
            LOGGER.error("unexpected db error: %s", ex)
            connection.close()
            raise StopIteration

    def get_transmitted_variants(self, **kwargs):
        self._copy_kwargs(kwargs)
        where = self._build_where()
        select = \
            "select " \
            "tsv.chrome as chr, " \
            "tsv.position as position, " \
            "tsv.variant as variant, "\
            "tsv.n_par_called as `all.nParCalled`, " \
            "tsv.prcnt_par_called as `all.prcntParCalled`, " \
            "tsv.n_alt_alls as `all.nAltAlls`, " \
            "tsv.alt_freq as `all.altFreq`, " \
            "tsv.effect_type as effectType, " \
            "tsv.effect_gene_all as `effectGene`, " \
            "tsv.effect_details as `effectDetails`, " \
            "tsv.seg_dups as `segDups`, " \
            "tsv.hw as `HW`, " \
            "tsv.ssc_freq as `SSC-freq`, " \
            "tsv.evs_freq as `EVS-freq`, " \
            "tsv.e65_freq as `E65-freq`, " \
            "tfv.family_id as `familyId`, " \
            "tfv.best as `bestState`, " \
            "tfv.counts as `counts` " \
            "from transmitted_familyvariant as tfv " \
            "left join transmitted_summaryvariant as tsv " \
            "on tfv.summary_variant_id = tsv.id " \
            "where {}".format(where)

        LOGGER.info("select: %s", select)
        try:
            connection, cursor = self.execute(select)
            v = cursor.fetchone()

            while v is not None:
                v["location"] = v["chr"] + ":" + str(v["position"])
                vr = self._build_variant_properties(v)

                yield vr
                v = cursor.fetchone()
        except StopIteration:
            connection.close()
        except Exception as ex:
            LOGGER.error("unexpected db error: %s", ex)
            connection.close()
            raise StopIteration
