'''
Created on Jul 7, 2015

@author: lubo
'''

# import h5py
import numpy as np
from api.variants.transmitted_variants import parse_family_data
from DAE import vDB
import gzip
from VariantsDB import parseGeneEffect
import itertools
import tables


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

    def build(self):
        filters = tables.Filters(complevel=1)

        with gzip.open(self.summary_filename, 'r') as sfh, \
            gzip.open(self.tm_filename, 'r') as tfh, \
                tables.open_file(self.h5_filename, "w",
                                 filters=filters) as h5fh:

            self.sfh = sfh
            self.tfh = tfh
            self.h5fh = h5fh

            self.summary_group = self.h5fh.create_group('/', 'summary',
                                                        'Summary Variants')
            self.summary_table = self.h5fh.create_table(
                                self.summary_group, 'variants',
                                SummaryVariants, 'Summary Variants Table')

            self.family_group = self.h5fh.create_group('/', 'family',
                                                       'Family Data')
            self.family_table = self.h5fh.create_table(
                                self.family_group, 'variant',
                                FamilyVariants, 'Family Variants Table')

            self.effect_group = self.h5fh.create_group('/', 'effect',
                                                       'Effect Data')
            self.effect_table = self.h5fh.create_table(
                                self.effect_group, 'effect',
                                GeneEffectVariants, 'Gene Effects Table')

            self.column_names = self.sfh.readline().rstrip().split('\t')
            self.summary_row = self.summary_table.row
            self.family_row = self.family_table.row
            self.effect_row = self.effect_table.row

            self.snrow = 0
            self.fnrow = 0
            self.enrow = 0

            self.tfh.readline()  # skip file header

            self.build_mainloop()

            self.summary_table.cols.line_number.create_index()

            # self.summary_table.cols.chrome.create_index()
            # self.summary_table.cols.position.create_index()

            # self.summary_table.cols.variant_type.create_index()
            # self.summary_table.cols.effect_type.create_index()

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

    def build_family_table(self, vals):
        family_data = vals['familyData']
        pfd = self.load_parse_family_data(family_data)

        fbegin = self.fnrow
        for fid, bs, c in pfd:
            self.family_row['fid'] = fid
            self.family_row['best'] = bs
            self.family_row['counts'] = c
            self.family_row['vrow'] = self.snrow
            self.family_row.append()
            self.fnrow += 1

        fend = self.fnrow
        return fbegin, fend

    def build_effect_table(self, vals):
        gene_effects = parseGeneEffect(vals['effectGene'])
        ebegin = self.enrow

        for index, ge in enumerate(gene_effects):
            if index == 0:
                self.summary_row['effect_gene'] = ge['sym']

            self.effect_row['symbol'] = ge['sym']
            et = EFFECT_TYPES[ge['eff']]
            self.effect_row['effect'] = et

            self.effect_row['vrow'] = self.snrow

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

    def build_summary_frequencies(self, vals):
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

            fbegin, fend = self.build_family_table(vals)
            self.summary_row['fbegin'] = fbegin
            self.summary_row['fend'] = fend

            ebegin, eend = self.build_effect_table(vals)
            self.summary_row['ebegin'] = ebegin
            self.summary_row['eend'] = eend
            self.summary_row['elen'] = eend - ebegin

            self.build_summary_frequencies(vals)

            self.summary_row.append()

            if self.snrow % 10000 == 0:
                self.summary_table.flush()
                self.family_table.flush()
                print self.snrow,
            self.snrow += 1


class TransmissionStudyQuery(object):
    filters = tables.Filters(complevel=1)

    def __init__(self, study_name):
        self.study_name = study_name
        self.h5_filename = "{}.hdf5".format(self.study_name)
        self.h5fh = tables.open_file(self.h5_filename, "r",
                                     filters=self.filters)

    def close(self):
        self.h5fh.close()

    def h5f_load_synonymous_test(self):
        table = self.h5fh.root.summary.variants
        etable = self.h5fh.root.effect.effect

        et = EFFECT_TYPES.synonymous
        where = '(effect_type == {}) & (n_alt_alls == 1) & ' + \
            ' (elen == 1)'.format(et)
        res = [set(x['effect_gene']) for x in table.where(where)]

        where = '(n_alt_alls == 1) & (elen > 1)'
        mres = table.read_where(where)
        for ms in mres:
            effect_genes = [sym for (et, sym, _)
                            in etable[ms['ebegin']: ms['eend']]
                            if et == EFFECT_TYPES.synonymous]
            if effect_genes:
                res.append(set(effect_genes))
        return res

    def dae_load_synonymous_test(self):
        transmitted_study = vDB.get_study(self.study_name)
        vs = transmitted_study.get_transmitted_summary_variants(
                ultraRareOnly=True,
                effectTypes="synonymous")
        return [v for v in vs]

    def h5f_load_synonymous_test2(self):
        etable = self.h5fh.root.effect.effect
        evar = etable.read_where('(effect == 16)')
        vrows = [er[0] for er in itertools.groupby(evar, lambda r: r[2])]
        vtable = self.h5fh.root.summary.variants
        vs = vtable[vrows]
        ur = vs[np.all([vs['n_par_called'] > 600,
                        vs['n_alt_alls'] == 1,
                        vs['alt_freq'] < 5], axis=0)]
        return ur

    def h5f_load_synonymous_test3(self):
        etable = self.h5fh.root.effect.effect
        where = '(effect == 16) & (n_par_called > 600) & ' + \
            '(n_alt_alls == 1) & (alt_freq < 5)'
        evar = etable.read_where(where)
        vrows = np.unique(evar['vrow'])
        vtable = self.h5fh.root.summary.variants
        vs = vtable[vrows]
        return vs


if __name__ == '__main__':
    # build_summary('w1202s766e611')
    builder = TransmissionIndexBuilder('w1202s766e611')
    builder.build()

    # query = TransmissionStudyQuery('w1202s766e611')
    # print (len(query.h5f_load_synonymous_test()))
    # print (len(query.dae_load_synonymous_test()))
