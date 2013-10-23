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


