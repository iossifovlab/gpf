'''
Created on Jul 7, 2015

@author: lubo
'''
from DAE import vDB
import tables
import gzip
from api.variants.hdf5_query import EFFECT_TYPES, VARIANT_TYPES, GENDER_TYPES
from api.variants.transmitted_variants import parse_family_data
from Variant import parseGeneEffect, Variant
# import itertools
# import numpy as np
import copy
# from query_variants_bak import augment_vars
# from query_variants_bak import augment_vars


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
    family_id = tables.StringCol(16)
    best = tables.StringCol(16)
    counts = tables.StringCol(64)
    vrow = tables.Int64Col()
    index = tables.Int64Col()

    in_mom = tables.BoolCol()
    in_dad = tables.BoolCol()

    in_prb = tables.BoolCol()
    in_prb_gender = tables.EnumCol(GENDER_TYPES,
                                   'M', base='uint8')
    in_sib = tables.BoolCol()
    in_sib_gender = tables.EnumCol(GENDER_TYPES,
                                   'M', base='uint8')


class GeneEffectVariants(tables.IsDescription):
    symbol = tables.StringCol(32)
    effect_type = tables.EnumCol(EFFECT_TYPES,
                                 'intergenic', base='uint8')
    variant_type = tables.EnumCol(VARIANT_TYPES,
                                  'sub', base='uint8')
    vrow = tables.Int64Col()

    n_par_called = tables.Int16Col()  # 'all.nParCalled'
    n_alt_alls = tables.Int16Col()  # 'all.nAltAlls'
    alt_freq = tables.Float16Col()  # 'all.altFreq'


class TransmissionIndexBuilder(object):

    def __init__(self, study_name):
        self.study_name = study_name

        self.study = vDB.get_study(self.study_name)

        self.summary_filename = self.study.vdb._config.get(
                    self.study._configSection,
                    'transmittedVariants.indexFile') + ".txt.bgz"
        self.tm_filename = self.study.vdb._config.get(
                self.study._configSection,
                'transmittedVariants.indexFile') + "-TOOMANY.txt.bgz"

        self.h5_filename = "{}.hdf5".format(self.study_name)

    def build_variants_structure(self):
        self.variants_group = self.h5fh.create_group('/', 'variants',
                                                     'Variants Group')
        self.summary_table = self.h5fh.create_table(
            self.variants_group, 'summary',
            SummaryVariants, 'Summary Variants Table')
        self.family_table = self.h5fh.create_table(
            self.variants_group, 'family',
            FamilyVariants, 'Family Variants Table')
        self.effect_table = self.h5fh.create_table(
            self.variants_group, 'effect',
            GeneEffectVariants, 'Gene Effects Table')

        self.summary_row = self.summary_table.row
        self.family_row = self.family_table.row
        self.effect_row = self.effect_table.row

        self.snrow = 0
        self.fnrow = 0
        self.enrow = 0

    def build_families_structure(self):
        self.families_group = self.h5fh.create_group('/', 'families',
                                                     'Families Group')
        for familyId in self.study.families:
            self.h5fh.create_table(self.families_group,
                                   'f{}'.format(familyId),
                                   FamilyVariants,
                                   'Per Family Variants Table')

    def build(self):
        filters = tables.Filters(complevel=1)

        with gzip.open(self.summary_filename, 'r') as sfh, \
            gzip.open(self.tm_filename, 'r') as tfh, \
                tables.open_file(self.h5_filename, "w",
                                 filters=filters) as h5fh:

            self.sfh = sfh
            self.tfh = tfh
            self.h5fh = h5fh

            self.build_variants_structure()
            # self.build_families_structure()

            self.column_names = self.sfh.readline().rstrip().split('\t')
            self.tfh.readline()  # skip file header

            self.build_mainloop()

    def load_parse_family_data(self, family_data):
        if family_data != 'TOOMANY':
            pfd = parse_family_data(family_data)
        else:
            fline = self.tfh.readline()
            ch, pos, var, families_data = fline.strip().split('\t')
            pos = int(pos)
            pfd = parse_family_data(families_data)
            assert ch == self.summary_row['chrome'] and \
                pos == self.summary_row['position'] and \
                var == self.summary_row['variant']
        return pfd

    def build_inparent(self, row, vs):
        from_parent = vs.fromParentS
        if 'mom' in from_parent:
            row['in_mom'] = 1
        if 'dad' in from_parent:
            row['in_dad'] = 1

    def build_inchild(self, row, vs):
        in_child = vs.inChS
        if 'prb' in in_child:
            row['in_prb'] = 1
            row['in_prb_gender'] = GENDER_TYPES[in_child[3]]
        if 'sib' in in_child:
            row['in_sib'] = 1
            gender = None
            if in_child.startswith('sib'):
                gender = GENDER_TYPES[in_child[3]]
            else:
                gender = GENDER_TYPES[in_child[7]]
            assert gender is not None
            row['in_sib_gender'] = gender

    def build_family_row(self, row, vals, vs):
        row['family_id'] = vs.familyId
        row['best'] = vs.bestStStr
        row['counts'] = vs.countsStr
        row['vrow'] = self.snrow
        row['index'] = self.fnrow

        self.build_inchild(row, vs)
        self.build_inparent(row, vs)

        row.append()

    def build_family_table(self, vals, summary_variant):
        family_data = vals['familyData']
        pfd = self.load_parse_family_data(family_data)

        fbegin = self.fnrow
        for fid, bs, c in pfd:
            vs = self.create_family_variant(summary_variant, (fid, bs, c))
            self.build_family_row(self.family_row, vals, vs)
            self.fnrow += 1

        fend = self.fnrow
        return fbegin, fend

    def build_effect_table(self, vals):
        gene_effects = parseGeneEffect(vals['effectGene'])
        ebegin = self.enrow
        vt = vals['variant'][0:3]

        for index, ge in enumerate(gene_effects):
            if index == 0:
                self.summary_row['effect_gene'] = ge['sym']
                # self.family_row['effect_gene'] = ge['sym']

            self.effect_row['symbol'] = ge['sym']
            et = EFFECT_TYPES[ge['eff']]
            self.effect_row['effect_type'] = et

            self.effect_row['vrow'] = self.snrow
            self.effect_row['variant_type'] = VARIANT_TYPES[vt]
            self.effect_row['n_par_called'] = int(vals['all.nParCalled'])
            self.effect_row['n_alt_alls'] = int(vals['all.nAltAlls'])
            self.effect_row['alt_freq'] = float(vals['all.altFreq'])

            self.effect_row.append()
            self.enrow += 1
        eend = self.enrow
        return ebegin, eend

    @staticmethod
    def safe_float(s):
        if s.strip() == '':
            return float('NaN')
        else:
            return float(s)

    def build_summary_row_frequencies(self, vals):
        self.summary_row['n_par_called'] = int(vals['all.nParCalled'])
        self.summary_row['n_alt_alls'] = int(vals['all.nAltAlls'])
        self.summary_row['alt_freq'] = float(vals['all.altFreq'])

        self.summary_row['prcnt_par_called'] = \
            float(vals['all.prcntParCalled'])
        self.summary_row['seg_dups'] = int(vals['segDups'])
        self.summary_row['hw'] = float(vals['HW'])
        self.summary_row['ssc_freq'] = self.safe_float(vals['SSC-freq'])
        self.summary_row['evs_freq'] = self.safe_float(vals['EVS-freq'])
        self.summary_row['e65_freq'] = self.safe_float(vals['E65-freq'])

    def create_summary_variant(self, vals):
        vals["location"] = vals["chr"] + ":" + vals["position"]
        v = Variant(vals)
        v.study = self.study
        if self.summary_row['n_alt_alls'] == 1:
            v.popType = 'ultraRare'
        else:
            v.popType = 'common'
        return v

    def create_family_variant(self, vs, family_data):
        v = copy.copy(vs)
        v.atts = {kk: vv for kk, vv in vs.atts.items()}
        fid, bs, counts = family_data
        v.atts['familyId'] = fid
        v.atts['bestState'] = bs
        v.atts['counts'] = counts

        return v

    def build_mainloop(self):
        for line in self.sfh:
            data = line.strip("\r\n").split("\t")
            vals = dict(zip(self.column_names, data))
            self.summary_row['line_number'] = self.snrow
            self.summary_row['chrome'] = vals['chr']
            self.summary_row['position'] = int(vals['position'])
            self.summary_row['variant'] = vals['variant']
            vt = vals['variant'][0:3]
            et = vals['effectType']

            self.summary_row['variant_type'] = VARIANT_TYPES[vt]
            self.summary_row['effect_type'] = EFFECT_TYPES[et]
            self.build_summary_row_frequencies(vals)

            vs = self.create_summary_variant(vals)

            fbegin, fend = self.build_family_table(vals, vs)
            self.summary_row['fbegin'] = fbegin
            self.summary_row['fend'] = fend

            ebegin, eend = self.build_effect_table(vals)
            self.summary_row['ebegin'] = ebegin
            self.summary_row['eend'] = eend
            self.summary_row['elen'] = eend - ebegin

            self.summary_row.append()
            # print self.snrow
            if self.snrow % 10000 == 0:
                self.summary_table.flush()
                self.family_table.flush()
                self.effect_table.flush()
                print self.snrow
            self.snrow += 1

        self.summary_table.flush()
        self.family_table.flush()
        self.effect_table.flush()


if __name__ == '__main__':

    builder = TransmissionIndexBuilder('w1202s766e611')
    builder.build()
