'''
Created on Jun 5, 2015

@author: lubo
'''
from DAE import vDB
import gzip
import pandas as pd
import numpy as np
from Variant import parseGeneEffect
import pysam
#import numba


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
    df = read_summary_df('w1202s766e611')
    return df


def read_summary_df(study_name):

    global dt
    
    ts = vDB.get_study(study_name)
    fname = ts.vdb._config.get(ts._configSection,
                    'transmittedVariants.indexFile' ) + ".txt.bgz"
    
    f = gzip.open(fname)
    df = pd.read_csv(f, sep='\t', dtype=dt)
    f.close()
    
    vec_parse_gene_effect = np.vectorize(parseGeneEffect)
    df.effectGeneParsed = np.apply_along_axis(vec_parse_gene_effect,
                                        0, 
                                        df.effectGene)
    
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


def filter_summary_regions_df(df, regions):
    regs = regions_splitter(regions)
    res = []
    for (chrome, beg, end) in regs:
        cdf = df[df.chr == chrome]
        idf = np.all([cdf.position >= beg, cdf.position <= end],0)
        pdf = cdf[idf]
        res.append(pdf)
        
    return pd.concat(res)

def filter_summary_parents_called(df, minParentsCalled=0):
    if minParentsCalled and minParentsCalled!=-1:
        return df[df['all.nParCalled']>=minParentsCalled]
    else:
        return df


def filter_summary_alt_freq_prcnt(df, minAltFreqPercnt=-1, maxAltFreqPrcnt=5):
    if minAltFreqPercnt != -1 and maxAltFreqPrcnt != -1:
        idf = np.all([df['all.altFreq'] > minAltFreqPercnt, 
                      df['all.altFreq'] < maxAltFreqPrcnt], 0)
        return df[idf]
    elif minAltFreqPercnt != -1:
        idf = df['all.altFreq'] > minAltFreqPercnt
        return df[idf]
    elif maxAltFreqPrcnt != -1:
        idf = df['all.altFreq'] < maxAltFreqPrcnt
        return df[idf]
    else:
        return df

    
def filter_summary_ultra_rare(df, ultraRareOnly=False):
    return df[df['all.nAltAlls'] == 1]


def filter_summary_variant_types(df, variantTypes):
    vf = np.vectorize(lambda v: v[0:3] in variantTypes)
    idf = vf(df.variant)
    return df[idf]


def build_gene_effect_filter(effectTypes, geneSyms):
    if effectTypes and geneSyms:
        def _filter_gene_effs_and_syms(geneEffects):
            res = [x for x in geneEffects 
                   if x['eff'] in effectTypes and
                   x['sym'] in geneSyms]
            return res if res else False

        return _filter_gene_effs_and_syms
    
    elif effectTypes:
        def _filter_gene_effs(geneEffects):
            res = [x for x in geneEffects if x['eff'] in effectTypes]
            return res if res else False
        
        return _filter_gene_effs
    
    elif geneSyms:
        def _filter_gene_syms(geneEffects):
            res = [x for x in geneEffects if x['sym'] in geneSyms]
            return res if res else False
        
        return _filter_gene_syms
    else:
        return (lambda _: False)

    
def filter_summary_gene_effect(df, effectTypes, geneSyms):
    f = build_gene_effect_filter(effectTypes, geneSyms)
    vf = np.vectorize(f)
    idf = np.apply_along_axis(vf, 0, df.effectGene)
    
    return df[idf]


def read_toomany_df(study_name):
    ts = vDB.get_study(study_name)
    fname = ts.vdb._config.get(ts._configSection, 
                'transmittedVariants.indexFile' ) \
                + "-TOOMANY.txt.bgz"

    tbf = pysam.Tabixfile(fname)
    
    return tbf

CN_CHROME = 0
CN_POSITION = 1
CN_VARIANT = 2
CN_FAMILY_DATA = 3


def load_toomany_family_data(tbf, row):
    chrome = row[CN_CHROME]
    position = row[CN_POSITION]
    variant = row[CN_VARIANT]
    
    l = tbf.fetch(chrome, position-1, position)
    l = l.next()
    # print("tbf fetch result: {}".format(l))
    l = l.strip().split('\t')
    # print("tbf fetch split: {}".format(l))
    tm_chrome, tm_pos, tm_variant, tm_families_data = l 
    if tm_chrome != chrome:
        raise ValueError("chomes doesn't match: {}, {}".format(chrome, tm_chrome))
    if int(tm_pos) != position:
        raise ValueError("position doesn't match: {}, {}".format(position, tm_pos))
    if tm_variant != variant:
        raise ValueError("chomes doesn't match: {}, {}".format(chrome, tm_chrome))
    return parse_family_data(tm_families_data)


#@numba.jit
def parse_family_data(fmsData):
    res = []
    for fmData in fmsData.split(';'):
        cs = fmData.split(':')
        if len(cs) != 3:
            raise ValueError("Wrong family data format {}".format(fmData))
        res.append(cs)
    return res


def parse_toomany_data(tbf, row):
    if row[CN_FAMILY_DATA]!='TOOMANY':
        raise ValueError("parse toomany row expects 'TOOMANY' in familyData")
    
    
