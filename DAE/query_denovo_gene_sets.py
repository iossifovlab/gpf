'''
Created on May 27, 2015

@author: lubo
'''
from DAE import vDB
from DAE import giDB

from GeneTerms import GeneTerms
from itertools import groupby

def set_genes(geneSetDef):
    gtId,tmId = geneSetDef.split(":")
    return set(giDB.getGeneTerms(gtId).t2G[tmId].keys())

def genes(dnvStds, inChild,effectTypes, nvIQ, inGenesSet=None,minIQ=None,maxIQ=None):
    vs = vDB.get_denovo_variants(dnvStds,
                                 effectTypes=effectTypes,
                                 inChild=inChild,
                                 geneSyms=inGenesSet)

    if not (minIQ or maxIQ):
        return {ge['sym'] for v in vs for ge in v.requestedGeneEffects}
    if minIQ:
        return {ge['sym']
                for v in vs for ge in v.requestedGeneEffects
                    if v.familyId in nvIQ and nvIQ[v.familyId]>=minIQ }
    if maxIQ:
        return {ge['sym'] 
                    for v in vs for ge in v.requestedGeneEffects
                    if v.familyId in nvIQ and nvIQ[v.familyId] < maxIQ }

def genes_test_default(denovo_studies, in_child, effect_types, gene_syms=None):
    vs = vDB.get_denovo_variants(denovo_studies,
                                 effectTypes=effect_types,
                                 inChild=in_child,
                                 geneSyms=gene_syms)
    return {ge['sym'] for v in vs for ge in v.requestedGeneEffects}

def genes_test_with_measure(denovo_studies, 
                            in_child=None,
                            effect_types=None,
                            gene_set=None,
                            measure=None,
                            mmax=None,
                            mmin=None):
    
    vs = vDB.get_denovo_variants(denovo_studies,
                                 effectTypes=effect_types,
                                 inChild=in_child,
                                 geneSyms=gene_set)

    if not (mmin or mmax):
        return {ge['sym'] for v in vs for ge in v.requestedGeneEffects}
    if mmin and measure:
        return {ge['sym']
                for v in vs for ge in v.requestedGeneEffects
                    if v.familyId in measure and measure[v.familyId]>=mmin }
    if mmax:
        return {ge['sym'] 
                    for v in vs for ge in v.requestedGeneEffects
                    if v.familyId in measure and measure[v.familyId] < mmax }
    return None

def genes_test_recurrent_and_single(
            denovo_studies, 
            in_child=None,
            effect_types=None,
            gene_set=None):
    
    vs = vDB.get_denovo_variants(denovo_studies,
                                 effectTypes=effect_types,
                                 inChild=in_child,
                                 geneSyms=gene_set)
    gnSorted = sorted([[ge['sym'], v] 
        for v in vs for ge in v.requestedGeneEffects ])
    sym2Vars = { sym: [ t[1] for t in tpi] 
        for sym, tpi in groupby(gnSorted, key=lambda x: x[0]) }
    sym2FN = { sym: len(set([v.familyId for v in vs])) 
        for sym, vs in sym2Vars.items() }
    return ({g for g,nf in sym2FN.items() if nf>1 }, 
            {g for g,nf in sym2FN.items() if nf==1 })


def get_measure(measure_name):
    from DAE import phDB
    strD = dict(zip(phDB.families,phDB.get_variable(measure_name)))
    # fltD = {f:float(m) for f,m in strD.items() if m!=''}
    fltD = {}
    for f,m in strD.items():
        try:
            # mf = float(m)
            # if mf>70:
            fltD[f] = float(m)
        except:
            pass
    return fltD


def get_denovo_sets(denovo_studies):
    r = GeneTerms()
    r.geneNS = "sym"

    nvIQ = get_measure('pcdv.ssc_diagnosis_nonverbal_iq')

    def addSet(setname, genes,desc=None):
        if not genes:
            return
        if desc:
            r.tDesc[setname] = desc
        else:
            r.tDesc[setname] = setname
        for gSym in genes:
            r.t2G[setname][gSym]+=1
            r.g2T[gSym][setname]+=1

    autisim = [dst for dst in denovo_studies 
        if dst.get_attr('study.phenotype') == 'autism']
    chd = [dst for dst in denovo_studies 
        if dst.get_attr('study.phenotype') == 'congenital heart disease']
    epilepsy = [dst for dst in denovo_studies 
        if dst.get_attr('study.phenotype') == 'epilepsy']
    intelectual_disability = [dst for dst in denovo_studies 
        if dst.get_attr('study.phenotype') == 'intelectual disability']
    schizophrenia = [dst for dst in denovo_studies 
        if dst.get_attr('study.phenotype') == 'schizophrenia']
    
    def recSingleGenes(stds, inChild,effectTypes):
        vs = vDB.get_denovo_variants(stds, effectTypes=effectTypes, inChild=inChild)

        gnSorted = sorted([[ge['sym'], v] 
                for v in vs for ge in v.requestedGeneEffects ])
        sym2Vars = { sym: [ t[1] for t in tpi] 
                for sym, tpi in groupby(gnSorted, key=lambda x: x[0]) }
        sym2FN = { sym: len(set([v.familyId for v in vs])) 
                for sym, vs in sym2Vars.items() }
        return ({g for g,nf in sym2FN.items() if nf>1 }, 
                {g for g,nf in sym2FN.items() if nf==1 })


    addSet("prb.LoF",             genes(denovo_studies, 'prb' ,'LGDs', nvIQ))
    recPrbLGDs, sinPrbLGDs = recSingleGenes(denovo_studies, 'prb' ,'LGDs')
    addSet("prb.LoF.Recurrent",   recPrbLGDs)
    addSet("prb.LoF.Single",      sinPrbLGDs)

    addSet("prb.LoF.Male",        genes(denovo_studies, 'prbM','LGDs', nvIQ))
    addSet("prb.LoF.Female",      genes(denovo_studies, 'prbF','LGDs', nvIQ))

    addSet("prb.LoF.LowIQ",       genes(denovo_studies, 'prb','LGDs', nvIQ, maxIQ=90))
    addSet("prb.LoF.HighIQ",      genes(denovo_studies, 'prb','LGDs', nvIQ, minIQ=90))

    addSet("prb.LoF.FMRP",        genes(denovo_studies, 'prb','LGDs', nvIQ, set_genes("main:FMR1-targets")))
    # addSet("prbLGDsInCHDs",     genes('prb','LGDs',set("CHD1,CHD2,CHD3,CHD4,CHD5,CHD6,CHD7,CHD8,CHD9".split(','))))

    addSet("prb.Missense",        genes(denovo_studies, 'prb', 'missense', nvIQ))
    addSet("prb.Missense.Male",   genes(denovo_studies, 'prbM', 'missense', nvIQ))
    addSet("prb.Missense.Female", genes(denovo_studies, 'prbF', 'missense', nvIQ))
    addSet("prb.Synonymous",      genes(denovo_studies, 'prb', 'synonymous', nvIQ))

    recPrbCNVs, sinPrbCNVs = recSingleGenes(denovo_studies, 'prb' ,'CNVs')
    addSet("prb.CNV.Recurrent",     recPrbCNVs)

    addSet("prb.CNV",   genes(denovo_studies, 'prb' ,'CNVs', nvIQ))
    addSet("prb.Dup",   genes(denovo_studies, 'prb' ,'CNV+', nvIQ))
    addSet("prb.Del",   genes(denovo_studies, 'prb' ,'CNV-', nvIQ))

    addSet("sib.LoF",             genes(denovo_studies, 'sib', 'LGDs', nvIQ))
    addSet("sib.Missense",        genes(denovo_studies, 'sib', 'missense', nvIQ))
    addSet("sib.Synonymous",      genes(denovo_studies, 'sib', 'synonymous', nvIQ))

    addSet("sib.CNV",   genes(denovo_studies, 'sib' ,'CNVs', nvIQ))
    addSet("sib.Dup",   genes(denovo_studies, 'sib' ,'CNV+', nvIQ))
    addSet("sib.Del",   genes(denovo_studies, 'sib' ,'CNV-', nvIQ))

    '''
    addSet("A",      recPrbLGDs, "recPrbLGDs")
    addSet("B",      genes('prbF','LGDs'), "prbF")
    addSet("C",      genes('prb','LGDs',set_genes("main:FMR1-targets")), "prbFMRP")
    addSet("D",      genes('prb','LGDs',maxIQ=90),"prbML")
    addSet("E",      genes('prb','LGDs',minIQ=90),"prbMH")

    addSet("AB",     set(r.t2G['A']) | set(r.t2G['B']))
    addSet("ABC",    set(r.t2G['A']) | set(r.t2G['B'])  | set(r.t2G['C']))
    addSet("ABCD",   set(r.t2G['A']) | set(r.t2G['B'])  | set(r.t2G['C'])  | set(r.t2G['D']) )
    addSet("ABCDE",   set(r.t2G['A']) | set(r.t2G['B'])  | set(r.t2G['C'])  | set(r.t2G['D']) | set(r.t2G['E']) )
    '''


    return r

def get_denovo_studies_by_phenotype():
    all_denovo_studies = vDB.get_studies("ALL WHOLE EXOME")
    studies = {
        # "all": all_denovo_studies,
        "autism": 
            [dst for dst in all_denovo_studies 
             if dst.get_attr('study.phenotype') == 'autism'],
        'congenital heart disease':
            [dst for dst in all_denovo_studies 
             if dst.get_attr('study.phenotype') == 'congenital heart disease'],
               
        "epilepsy":
            [dst for dst in all_denovo_studies 
             if dst.get_attr('study.phenotype') == 'epilepsy'],
               
        'intelectual disability':
             [dst for dst in all_denovo_studies 
              if dst.get_attr('study.phenotype') == 'intelectual disability'],
        
        'schizophrenia':
            [dst for dst in all_denovo_studies 
             if dst.get_attr('study.phenotype') == 'schizophrenia']}
    
    return studies

def prb_tests_per_phenotype():
    nvIQ = get_measure('pcdv.ssc_diagnosis_nonverbal_iq')
    
    prb_tests = {
        "LoF": lambda studies: genes_test_default(studies, in_child='prb', effect_types='LGDs'),
        "LoF.Male": lambda studies: genes_test_default(studies, in_child='prbM', effect_types='LGDs'),
        "LoF.Female": lambda studies: genes_test_default(studies, in_child='prbF', effect_types='LGDs'),
        
        "LoF.LowIQ": lambda studies: genes_test_with_measure(studies, in_child='prb', effect_types='LGDs', measure=nvIQ, mmax=90),
        "LoF.HighIQ": lambda studies: genes_test_with_measure(studies, in_child='prb', effect_types='LGDs', measure=nvIQ, mmin=90),
        
        "LoF.FMRP": lambda studies: genes_test_default(studies, in_child='prb', effect_types='LGDs', gene_syms=set_genes("main:FMR1-targets")),
        
        "Missense": lambda studies: genes_test_default(studies, in_child="prb", effect_types="missense"),
        "Missense.Male": lambda studies: genes_test_default(studies, in_child="prbM", effect_types="missense"),
        "Missense.Female": lambda studies: genes_test_default(studies, in_child="prbF", effect_types="missense"),
        
        "Synonymous": lambda studies: genes_test_default(studies, in_child="prb", effect_types="synonymous"),
        
        "CNV": lambda studies: genes_test_default(studies, in_child="prb", effect_types="CNV"),
        "Dup": lambda studies: genes_test_default(studies, in_child="prb", effect_types="CNV+"),
        "Del": lambda studies: genes_test_default(studies, in_child="prb", effect_types="CNV-"),
        
    }
    return prb_tests

def prb_default_tests_by_phenotype(all_studies):
    prb_default_tests = prb_tests_per_phenotype()
    res = {}
    for phenotype, studies in all_studies.items():
        res[phenotype] = dict([(test_name, test_filter(studies)) 
                               for test_name, test_filter in prb_default_tests.items()])
        
    return res


def get_denovo_gene_sets_by_phenotype():
    studies = get_denovo_studies_by_phenotype()
    
    pass