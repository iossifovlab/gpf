'''
Created on May 27, 2015

@author: lubo
'''
from DAE import vDB
from DAE import giDB

from itertools import groupby
from GeneTerms import GeneTerms

def set_genes(geneSetDef):
    gtId, tmId = geneSetDef.split(":")
    return set(giDB.getGeneTerms(gtId).t2G[tmId].keys())

def genes_sets(denovo_studies,
               in_child=None,
               effect_types=None,
               gene_syms=None,
               measure=None,
               mmax=None,
               mmin=None):
    
    vs = vDB.get_denovo_variants(denovo_studies,
                                 effectTypes=effect_types,
                                 inChild=in_child,
                                 geneSyms=gene_syms)

    if not (mmin or mmax):
        return {ge['sym'] for v in vs for ge in v.requestedGeneEffects}
    if mmin and measure:
        return {ge['sym']
                for v in vs for ge in v.requestedGeneEffects
                    if v.familyId in measure and measure[v.familyId] >= mmin }
    if mmax and measure:
        return {ge['sym'] 
                    for v in vs for ge in v.requestedGeneEffects
                    if v.familyId in measure and measure[v.familyId] < mmax }
    return None

def genes_set_prepare_counting(
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
    return sym2FN

def genes_set_recurrent(
            denovo_studies,
            in_child=None,
            effect_types=None,
            gene_set=None):
    
    sym2FN = genes_set_prepare_counting(denovo_studies, in_child,
                                         effect_types, gene_set)
    return {g for g, nf in sym2FN.items() if nf > 1 }

def genes_set_single(
            denovo_studies,
            in_child=None,
            effect_types=None,
            gene_set=None):
    
    sym2FN = genes_set_prepare_counting(denovo_studies, in_child,
                                         effect_types, gene_set)
    return {g for g, nf in sym2FN.items() if nf == 1 }

def get_measure(measure_name):
    from DAE import phDB
    strD = dict(zip(phDB.families, phDB.get_variable(measure_name)))
    # fltD = {f:float(m) for f,m in strD.items() if m!=''}
    fltD = {}
    for f, m in strD.items():
        try:
            # mf = float(m)
            # if mf>70:
            fltD[f] = float(m)
        except:
            pass
    return fltD


def get_all_denovo_studies():
    whole_exome_studies = vDB.get_studies("ALL WHOLE EXOME") 
    ssc_studies = [] # vDB.get_studies("ALL SSC")
    
    all_denovo_studies = whole_exome_studies[:]

    [all_denovo_studies.append(study) 
     for study in ssc_studies if study not in whole_exome_studies]

    return all_denovo_studies


def filter_denovo_studies_by_phenotype(denovo_studies, phenotype):
    result = [dst for dst in denovo_studies 
              if dst.get_attr('study.phenotype') == phenotype]
    return result


def prb_set_per_phenotype():
    nvIQ = get_measure('pcdv.ssc_diagnosis_nonverbal_iq')
    
    prb_tests = {
        "LGDs": lambda studies: genes_sets(
                                        studies,
                                        in_child='prb',
                                        effect_types='LGDs'),

        "LGDs.Male": lambda studies: genes_sets(
                                        studies,
                                        in_child='prbM',
                                        effect_types='LGDs'),
        
        "LGDs.Female": lambda studies: genes_sets(
                                        studies,
                                        in_child='prbF',
                                        effect_types='LGDs'),
        
        "LGDs.Recurrent": lambda studies: genes_set_recurrent(
                                        studies,
                                        in_child="prb",
                                        effect_types="LGDs"),
                 
        "LGDs.WE.Recurrent": lambda studies: genes_set_recurrent(
                                        [st for st in studies 
                                         if st.get_attr('study.type') == 'WE'],
                                        in_child="prb",
                                        effect_types="LGDs"),
                 
        "LGDs.Single": lambda studies: genes_set_single(
                                        studies,
                                        in_child="prb",
                                        effect_types="LGDs"),
        
        "LGDs.LowIQ": lambda studies: genes_sets(
                                        studies,
                                        in_child='prb',
                                        effect_types='LGDs',
                                        measure=nvIQ,
                                        mmax=90),
                 
        "LGDs.HighIQ": lambda studies: genes_sets(
                                        studies,
                                        in_child='prb',
                                        effect_types='LGDs',
                                        measure=nvIQ,
                                        mmin=90),
        
        "LGDs.FMRP": lambda studies: genes_sets(
                                        studies,
                                        in_child='prb',
                                        effect_types='LGDs',
                                        gene_syms=set_genes("main:FMR1-targets")),
        
        "Missense.Recurrent": lambda studies: genes_set_recurrent(
                                        studies,
                                        in_child="prb",
                                        effect_types="missense"),
                 
        "Missense.WE.Recurrent": lambda studies: genes_set_recurrent(
                                        [st for st in studies 
                                         if st.get_attr('study.type') == 'WE'],
                                        in_child="prb",
                                        effect_types="missense"),

        "Missense": lambda studies: genes_sets(
                                        studies,
                                        in_child="prb",
                                        effect_types="missense"),
                 
        "Missense.Male": lambda studies: genes_sets(
                                        studies,
                                        in_child="prbM",
                                        effect_types="missense"),
                 
        "Missense.Female": lambda studies: genes_sets(
                                        studies,
                                        in_child="prbF",
                                        effect_types="missense"),
        
        "Synonymous.Recurrent": lambda studies: genes_set_recurrent(
                                        studies,
                                        in_child="prb",
                                        effect_types="synonymous"),

        "Synonymous.WE.Recurrent": lambda studies: genes_set_recurrent(
                                        [st for st in studies 
                                         if st.get_attr('study.type') == 'WE'],
                                        in_child="prb",
                                        effect_types="synonymous"),

        "Synonymous": lambda studies: genes_sets(
                                        studies,
                                        in_child="prb",
                                        effect_types="synonymous"),
        
        "CNV": lambda studies: genes_sets(
                                        studies,
                                        in_child="prb",
                                        effect_types="CNVs"),

        "CNV.Recurrent": lambda studies: genes_set_recurrent(
                                        studies,
                                        in_child="prb",
                                        effect_types="CNVs"),
        
        "Dup": lambda studies: genes_sets(
                                        studies,
                                        in_child="prb",
                                        effect_types="CNV+"),
        "Del": lambda studies: genes_sets(
                                        studies,
                                        in_child="prb",
                                        effect_types="CNV-"),
        
    }
    return prb_tests


def add_set(gene_terms, setname, genes, desc=None):
    if not genes:
        return
    if desc:
        gene_terms.tDesc[setname] = desc
    else:
        gene_terms.tDesc[setname] = setname
    for gsym in genes:
        gene_terms.t2G[setname][gsym] += 1
        gene_terms.g2T[gsym][setname] += 1


def build_prb_set_by_phenotype(denovo_studies, phenotype):
    phenotype_studies = filter_denovo_studies_by_phenotype(
                denovo_studies, phenotype)
    prb_tests = prb_set_per_phenotype()
    
    gene_terms = GeneTerms()
    
    for test_name, test_filter in prb_tests.items():
        add_set(gene_terms, test_name, test_filter(phenotype_studies))
        
    return gene_terms


def sib_sets(studies):
    
    
    res = {
        "LGDs": genes_sets(
                        studies,
                        in_child='sib',
                        effect_types='LGDs'),
        "LGDs.Recurrent": genes_set_recurrent(
                        studies,
                        in_child="sib",
                        effect_types="LGDs"),

        "LGDs.WE.Recurrent": genes_set_recurrent(
                        [st for st in studies 
                         if st.get_attr('study.type') == 'WE'],
                        in_child="sib",
                        effect_types="LGDs"),

        "Missense.Recurrent": genes_set_recurrent(
                        studies,
                        in_child='sib',
                        effect_types='missense'),

        "Missense.WE.Recurrent": genes_set_recurrent(
                        [st for st in studies 
                         if st.get_attr('study.type') == 'WE'],
                        in_child="sib",
                        effect_types="missense"),


        "Missense": genes_sets(
                        studies,
                        in_child='sib',
                        effect_types='missense'),
           
        "Synonymous": genes_sets(
                        studies,
                        in_child='sib',
                        effect_types='synonymous'),

        "Synonymous.Recurrent": genes_set_recurrent(
                        studies,
                        in_child='sib',
                        effect_types='synonymous'),

        "Synonymous.WE.Recurrent": genes_set_recurrent(
                        [st for st in studies 
                         if st.get_attr('study.type') == 'WE'],
                        in_child="sib",
                        effect_types="synonymous"),

        "CNV": genes_sets(
                        studies,
                        in_child='sib',
                        effect_types='CNVs'),
        "Dup": genes_sets(
                        studies,
                        in_child='sib',
                        effect_types='CNV+'),
        "Del": genes_sets(
                        studies,
                        in_child='sib',
                        effect_types='CNV-'),
    }
        
    return res

def build_sib_set(denovo_studies):
    gene_syms = sib_sets(denovo_studies)
    
    gene_terms = GeneTerms()
    
    for test_name, gene_set in gene_syms.items():
        add_set(gene_terms, test_name, gene_set)
        
    return gene_terms


def build_denovo_gene_sets():
    result = {}
    denovo_studies = get_all_denovo_studies()
    all_phenotypes = ['autism', 'congenital heart disease',
                       "epilepsy", 'intelectual disability', 'schizophrenia']
    for phenotype in all_phenotypes:
        gene_terms = build_prb_set_by_phenotype(denovo_studies, phenotype)
        result[phenotype]=gene_terms
        
    result['unaffected'] = build_sib_set(denovo_studies)
    
    return result
