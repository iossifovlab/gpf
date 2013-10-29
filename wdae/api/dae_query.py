import itertools

from django.conf import settings
  
from DAE import vDB
    
def prepare_inchild(data):
    if not data.has_key('inChild'):
        return None

    inChild=data['inChild']
    if inChild=='All' or inChild=='none' or inChild=='None':
        return None
    
    if inChild not in vDB.get_child_types():
        return None
    
    return inChild
    
    
def prepare_effect_types(data):
    if not data.has_key('effectTypes'):
        return None
    
    effect_type=data['effectTypes']
    if effect_type=='none' or effect_type == 'None' or effect_type is None:
        return None

    if effect_type not in vDB.get_effect_types():
        effect_type='All'
    
    if effect_type=='All':
        return ",".join(vDB.get_effect_types()[1:])
    
    return effect_type


def prepare_variant_types(data):
    if not data.has_key('variantTypes'):
        return None
    
    variant_types=data['variantTypes']
    if variant_types=='none' or variant_types == 'None' or variant_types is None:
        return None
    
    if variant_types not in vDB.get_variant_types():
        return None
    
    if variant_types == 'All':
        return None
    
    return variant_types

def prepare_family_ids(data):
    if not data.has_key('familyIds'):
        return None
    
    families=data['familyIds']
    if isinstance(families,str):
        if families.lower() == 'none' or families.lower() == 'all':
            return None
        else:
            return [s.strip() for s in families.split(',') if len(s.strip())>0]
    elif isinstance(families,list):
        return families
    else:
        return None

def __filter_gene_syms(gl):
    return [g for g in gl if g in settings.GENE_SYMS_SET]

def prepare_gene_syms(data):
    if not data.has_key('geneSyms'):
        return None
    
    gene_sym=data['geneSyms']
    if isinstance(gene_sym, list):
        gl=__filter_gene_syms(gene_sym)
        if not gl:
            return None
        else:
            return set(gl)
        
    elif isinstance(gene_sym, str):
        gl = [s.strip() for s in gene_sym.split(',') if len(s.strip())>0]
        gl = __filter_gene_syms(gl)
        if not gl:
            return None
        return set(gl)
    else:
        return None

def __filter_gene_set(gene_set):
    gs_id=gene_set['gs_id']
    gs_term=gene_set['gs_term']
    
    gs=None
    if gs_id.lower().strip()=='main':
        gs=settings.GENE_SETS_MAIN
    elif gs_id.lower().strip()=='go':
        gs=settings.GENE_SETS_GO
    elif gs_id.lower().strip()=='disease':
        gs=settings.GENE_SETS_DISEASE
    else:
        return None
    
    if gs_term not in gs.tDesc:
        return None
    
    gl=__filter_gene_syms(gs.t2G[gs_term].keys())

    if not gl:
        return None
        
    return set(gl)

    
def prepare_gene_sets(data):
    if not data.has_key('geneSet'):
        return None
     
    gene_set = data['geneSet']
    
    if isinstance(gene_set,dict):
        return __filter_gene_set(gene_set)
    elif isinstance(gene_set,str):
        return None
    else:
        return None

def prepare_denovo_studies(data):
    if not data.has_key('denovoStudies'):
        return None
    
    dl=data['denovoStudies']

    dst = [vDB.get_studies(str(d)) for d in dl]
    
    flatten=itertools.chain.from_iterable(dst)
    res=[st for st in flatten if st is not None]
    if not res:
        return None
     
    return res


def prepare_transmitted_studies(data):
    if not data.has_key('transmittedStudies'):
        return None
    
    tl=data['transmittedStudies']
    tst = [vDB.get_study(str(st)) for st in tl]
    
    res=[st for st in tst if st is not None]
    if not res:
        return None
     
    return res

def combine_gene_syms(data):
    gene_syms=prepare_gene_syms(data)
    gene_sets=prepare_gene_sets(data)

    if gene_syms is None:
        return gene_sets
    else:
        if gene_sets is None:
            return gene_syms
        else:
            return gene_sets.union(gene_syms)
    
#"minParentsCalled=600,maxAltFreqPrcnt=5.0,minAltFreqPrcnt=-1"

def __prepare_min_alt_freq_prcnt(data):
    minAltFreqPrcnt=-1.0
    if data.has_key('minAltFreqPrcnt'):
        try:
            minAltFreqPrcnt=float(str(data['minAltFreqPrcnt']))
        except:
            minAltFreqPrcnt=-1.0
    return minAltFreqPrcnt

def __prepare_max_alt_freq_prcnt(data):
    maxAltFreqPrcnt=5.0
    if data.has_key('maxAltFreqPrcnt'):
        try:
            maxAltFreqPrcnt=float(str(data['maxAltFreqPrcnt']))
        except:
            maxAltFreqPrcnt=5.0
    return maxAltFreqPrcnt
        

def __prepare_min_parents_called(data):
    minParentsCalled=600
    if data.has_key('minParentsCalled'):
        try:
            minParentsCalled=float(str(data['minParentsCalled']))
        except:
            minParentsCalled=600
    return minParentsCalled



def __prepare_ultra_rare(data):
    ultraRareOnly=None
    if data.has_key('ultraRareOnly'):
        if ultraRareOnly=='True' or ultraRareOnly=='true':
            ultraRareOnly=True
    return ultraRareOnly

def prepare_transmitted_filters(data):
    filters={'variantTypes':prepare_variant_types(data),
             'effectTypes':prepare_effect_types(data),
             'inChild':prepare_inchild(data),
             'familyIds':prepare_family_ids(data),
             'geneSyms':combine_gene_syms(data),
             'ultraRareOnly':__prepare_ultra_rare(data),
             'minParentsCalled':__prepare_min_parents_called(data),
             'minAltFreqPrcnt':__prepare_min_alt_freq_prcnt(data),
             'maxAltFreqPrcnt':__prepare_max_alt_freq_prcnt(data)
             }
    return filters

def prepare_denovo_filters(data):
        
    filters={'inChild':prepare_inchild(data),
             'variantTypes':prepare_variant_types(data),
             'effectTypes':prepare_effect_types(data),
             'familyIds':prepare_family_ids(data),
             'geneSyms':combine_gene_syms(data)}
    return filters

def dae_query_variants(data):
    print "dae_query_variants:",data
    variants=[]
    dstudies=prepare_denovo_studies(data)
    print "denovo studies:",dstudies
    
    if dstudies is not None:
        filters=prepare_denovo_filters(data)
        dvs=vDB.get_denovo_variants(dstudies,**filters)
        variants.append(dvs)
    
    tstudies=prepare_transmitted_studies(data)
    print "transmitted studies:",tstudies
    if tstudies is not None:
        filters=prepare_transmitted_filters(data)
        for study in tstudies:
            tvs=study.get_transmitted_variants(**filters)
            variants.append(tvs)

    return variants
    

from VariantsDB import mat2Str


def safe_vs(tf,vs,atts=[],sep="\t"):
    for line in generate_response(vs,atts,sep):
        tf.write(line)


def generate_response(vs,atts=[],sep="\t"):
    def ge2Str(gs):
        return "|".join( x['sym'] + ":" + x['eff'] for x in gs)

    mainAtts = "familyId studyName location variant bestSt fromParentS inChS counts geneEffect requestedGeneEffects popType".split()
    specialStrF = {"bestSt":mat2Str, "counts":mat2Str, "geneEffect":ge2Str, "requestedGeneEffects":ge2Str}

    yield (sep.join(mainAtts+atts)+"\n") 

    for v in vs:
        mavs = []
        for att in mainAtts:
            try:
                if att in specialStrF:
                    mavs.append(specialStrF[att](getattr(v,att)))
                else:
                    mavs.append(str(getattr(v,att)))
            except:
                mavs.append("")
                 
        tmp = sep.join(mavs + [str(v.atts[a]).replace(sep, ';') if a in v.atts else "" for a in atts]) 
        yield (tmp +"\n")




