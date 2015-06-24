'''
Created on Jun 5, 2015

@author: lubo
'''
from DAE import vDB
import gzip
import pandas as pd
import numpy as np


def just_test():
    study_names = vDB.get_study_names()
    print study_names
    studies = vDB.get_studies(','.join(study_names))
    print studies
    return [st for st in studies if st.has_transmitted]

def another_test():
    ts = vDB.get_study('w1202s766e611')
    fname = ts.vdb._config.get(ts._configSection, 
                'transmittedVariants.indexFile' ) \
                + "-TOOMANY.txt.bgz"
    print fname
    
    fname = ts.vdb._config.get(ts._configSection,
                    'transmittedVariants.indexFile' ) + ".txt.bgz"
    print fname

    return ts

dt = dict(
    [
        ('chr',               np.dtype('S2')),
        ('position',                np.int64),
        ('variant',                np.object),
        ('familyData',             np.object),
        ('all.nParCalled',          np.int64),
        ('all.prcntParCalled',    np.float64),
        ('all.nAltAlls',            np.int64),
        ('all.altFreq',           np.float64),
        ('effectType',             np.object),
        ('effectGene',             np.object),
        ('effectDetails',          np.object),
        ('segDups',                 np.int64),
        ('HW',                    np.float64),
        ('SSC-freq',              np.float64),
        ('EVS-freq',              np.float64),
        ('E65-freq',              np.float64),
    ])


def read_df():
    global dt

    ts = vDB.get_study('w1202s766e611')
    fname = ts.vdb._config.get(ts._configSection,
                    'transmittedVariants.indexFile' ) + ".txt.bgz"
    
    f = gzip.open(fname)
    df = pd.read_csv(f, sep='\t', dtype=dt)
    f.close()
    
    return df


def read_summary_df(study_name):

    global dt
    
    ts = vDB.get_study('w1202s766e611')
    fname = ts.vdb._config.get(ts._configSection,
                    'transmittedVariants.indexFile' ) + ".txt.bgz"
    
    f = gzip.open(fname)
    df = pd.read_csv(f, sep='\t', dtype=dt)
    f.close()
    
    return df

def regions_splitter(regions):
    regs = [r.strip() for r in regions.split(',')]
    reg_defs = []

    for r in regs:
        smcP = r.find(":")
        dsP = r.find("-")
        chrom = r[0:smcP].strip()
        beg = int(r[smcP+1:dsP])
        end = int(r[dsP+1:])
        if beg>=end:
            raise ValueError("wrong gene region: begin-end problem")
        
        reg_defs.append((chrom, beg, end))
        
    return reg_defs

def regions_matcher(regions):
    reg_defs = regions_splitter(regions)
    return lambda v: any([(chrom == v[0]
                           and v[1] >= beg
                           and v[1] <= end)
                                   for(chrom, beg, end) in reg_defs])

def filter_summary_regions_df(df, regions):
    regs = regions_splitter(regions)
    res = []
    for (chrome, beg, end) in regs:
        cdf = df[df.chr == chrome]
        idf = np.all([cdf.position > beg, cdf.position < end],0)
        pdf = cdf[idf]
        res.append(pdf)
        
    return pd.concat(res)

