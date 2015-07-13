'''
Created on Jul 7, 2015

@author: lubo
'''

# import h5py
import numpy as np
import collections
from api.variants.transmitted_variants import parse_family_data
from DAE import vDB
import gzip
from VariantsDB import parseGeneEffect


def build_position(fh, df):
    for chrome in np.unique(df.chr):
        dc = df[df.chr == chrome]

        dt = np.dtype([("position", np.int64), ("variant", np.dtype('S64'))])
        data = np.array(zip(dc.position.values, 
                         np.vectorize(np.str)(dc.variant.values)), dtype=dt)
        
        dset_name = "/position/{}".format(chrome)
        fh.create_dataset(dset_name, 
                          data=data,
                          chunks=True,
                          compression='gzip',
                          shuffle=True)


def build_family(fh, df):
    counter = collections.Counter()
    for fd in df.familyData:
        if fd == 'TOOMANY':
            continue
        pdf = parse_family_data(fd)
        for (fid, _bs, _c) in pdf:
            counter[fid] += 1
    print counter
    return counter


def build_toomany(fh, study_name):
    ts = vDB.get_study(study_name)
    fname = ts.vdb._config.get(ts._configSection, 
                'transmittedVariants.indexFile' ) \
                + "-TOOMANY.txt.bgz"
    f = gzip.open(fname,'r')
    fdsets = {}
    dt = np.dtype([('chr', np.dtype('S4')), 
                   ('position', np.int64),
                   ('variant', np.dtype('S64')),
                   ('best', np.dtype('S16')),
                   ('counts', np.dtype('S64'))])
    
    f.readline()
    ln = 0
    for line in f:
        print '.',
        ln += 1
        if ln % 100 == 0:
            print "\nline: ", ln, 
        if ln % 1000 == 0:
            print "\nline: flushing....", ln 
            fh.flush()
            
            
        row = line.strip().split('\t')
        chrome, pos, variant, families_data = row
        pos = int(pos)
        pfd = parse_family_data(families_data)
        for (fid, best, counts) in pfd:
            if fid not in fdsets:
                setname = "/family/{}".format(fid)
                dset = fh.create_dataset(setname, 
                                         dtype=dt, 
                                         shape=(1, 5), 
                                         maxshape=(None, 5))
                fdsets[fid] = dset
            else:
                dset = fdsets[fid]
                dset.resize( (dset.shape[0]+1, 5) )
            dset[-1] = (chrome, pos, variant, best, counts)
        

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
    chrome = tables.StringCol(3)
    position = tables.Int64Col()
    variant = tables.StringCol(45)
    variant_type = tables.EnumCol(VARIANT_TYPES,
                                  'sub', base='uint8')
    effect_type = tables.EnumCol(EFFECT_TYPES,
                                 'intergenic', base='uint8')
    fbegin = tables.Int64Col()
    fend = tables.Int64Col()
    ebegin = tables.Int64Col()
    eend = tables.Int64Col()
    
class FamilyVariants(tables.IsDescription):
    fid = tables.StringCol(16)
    best = tables.StringCol(16)
    counts = tables.StringCol(64)
    vrow = tables.Int64Col()
    
class GeneEffectVariants(tables.IsDescription):
    symbol = tables.StringCol(32)
    effect = tables.StringCol(32)
    vrow = tables.Int64Col()

class TransmissionIndexBuilder(object):
    def __init__(self, study_name):
        self.study_name = study_name

        self.study = vDB.get_study(self.study_name)
        
        self.summary_filename = self.study.vdb._config.get(
                    self.study._configSection,
                    'transmittedVariants.indexFile' ) + ".txt.bgz"
        self.tm_filename = self.study.vdb._config.get(
                self.study._configSection, 
                'transmittedVariants.indexFile' ) \
                + "-TOOMANY.txt.bgz"

        self.h5_filename = "{}.hdf5".format(self.study_name)


    def build(self):
        filters = tables.Filters(complevel=1)


        with gzip.open(self.summary_filename, 'r') as sfh, \
            gzip.open(self.tm_filename, 'r') as tfh, \
            tables.open_file(self.h5_filename, "w", filters=filters) as h5fh:
            
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

            self.tfh.readline() # skip file header  

            self.build_mainloop()
    
    def load_parse_family_data(self, family_data):
        if family_data != 'TOOMANY':
            pfd = parse_family_data(family_data)
        else:
            fline = self.tfh.readline()
            ch, pos, var, families_data = fline.strip().split('\t')
            pos = int(pos)
            pfd = parse_family_data(families_data)
            assert ch == self.summary_row['chrome'] and pos == self.summary_row['position'] and var == self.summary_row['variant']
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
        for ge in gene_effects:
            self.effect_row['symbol'] = ge['sym']
            self.effect_row['effect'] = ge['eff']
            self.effect_row['vrow'] = self.snrow
            self.effect_row.append()
            self.enrow += 1
        eend = self.enrow
        return ebegin, eend
    
    def build_mainloop(self):
        for line in self.sfh:
            data = line.strip("\r\n").split("\t")
            vals = dict(zip(self.column_names, data))
            
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

            self.summary_row.append()
            
            if self.snrow % 1000==0:
                self.summary_table.flush()
                self.family_table.flush()
                print self.snrow, 
            self.snrow += 1            


def build_summary(study_name):
    ts = vDB.get_study('w1202s766e611')
    
    fname = ts.vdb._config.get(ts._configSection,
                    'transmittedVariants.indexFile' ) + ".txt.bgz"

    tfname = ts.vdb._config.get(ts._configSection, 
                'transmittedVariants.indexFile' ) \
                + "-TOOMANY.txt.bgz"
    filters = tables.Filters(complevel=1)
                           
    with gzip.open(fname, 'r') as f, \
        gzip.open(tfname, 'r') as tf, \
        tables.open_file("experiment.hdf5", "w", filters=filters) as h5f:
        
        sgroup = h5f.create_group('/', 'summary', 'Summary Variants')
        stable = h5f.create_table(sgroup, 'variants', 
                                  SummaryVariants, 'Summary Variants Table')
        
        fgroup = h5f.create_group('/', 'family', 'Family Data')
        ftable = h5f.create_table(fgroup, 'variant',
                                  FamilyVariants, 'Family Variants Table')
        
        cols_names = f.readline().rstrip().split('\t')
        ln = 0
        srow = stable.row
        frow = ftable.row
        fnrow = 0
        
        tf.readline() # skip file header
        
        for line in f:
            
            data = line.strip("\r\n").split("\t")
            vals = dict(zip(cols_names, data))
            srow['chrome'] = vals['chr']
            srow['position'] = int(vals['position'])
            srow['variant'] = vals['variant']
            vt = vals['variant'][0:3]
            et = vals['effectType']
            
            srow['variant_type'] = VARIANT_TYPES[vt] 
            srow['effect_type'] = EFFECT_TYPES[et]
            
            snrow = ln

            family_data = vals['familyData']
            if family_data != 'TOOMANY':
                pfd = parse_family_data(family_data)
            else:
                fline = tf.readline()
                
                ch, pos, var, families_data = fline.strip().split('\t')
                pos = int(pos)
                pfd = parse_family_data(families_data)
                assert ch == srow['chrome'] and \
                    pos == srow['position'] and \
                    var == srow['variant']

                
            fbegin = fnrow
            for (fid, bs, c) in pfd:
                frow['fid'] = fid
                frow['best'] = bs
                frow['counts'] = c
                frow['vrow'] = snrow
                frow.append()
                fnrow += 1
            fend = fnrow
            
            srow['fbegin'] = fbegin
            srow['fend'] = fend
            srow.append()
            
            if ln % 1000==0:
                srow.table.flush()
                frow.table.flush()
                print ln, 
            ln += 1



if __name__ == '__main__':

    # build_summary('w1202s766e611')

    builder = TransmissionIndexBuilder('w1202s766e611')
    builder.build()

    


