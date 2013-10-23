from DAE import vDB


def prepare_denovo_studies(data):
    if not data.has_key('denovoStudies'):
        return []
    else:
        dl=data['denovoStudies']
        dst=[]
        try:
            dst = [vDB.get_study(str(d)) for d in dl]
        except:
            print "The denovo study: %s does not exists..." % ' '.join(dl) 
        return dst
    
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
    if not data.has_key('familiesList'):
        return None
    
    families=data['familiesList']
    if isinstance(families,str):
        if families.lower() == 'none' or families.lower() == 'all':
            return None
        else:
            return [s.strip() for s in families.split(',') if len(s.strip())>0]
    elif isinstance(families,list):
        return families
    else:
        return None

def prepare_gen_syms(data):
    pass
