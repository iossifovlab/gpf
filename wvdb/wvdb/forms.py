from django import forms
from DAE import *

class VariantForm(forms.Form):

        
    geneSymbolFld = forms.CharField(widget=forms.Textarea(attrs={"rows":2,"cols":60}))
    geneSymbolFld.label = "Gene Symbols"
    geneSymbolFld.required = False
    
    denovo_choices = [('none','none')]
    choices = [(x,x) for x in vDB.getDenovoStudies()]
    choices.extend([(x,x) for x in vDB.getStudyGroups()])
    
    denovo_choices.extend(choices)

    denovoStudyFld = forms.ChoiceField(choices=denovo_choices)
    denovoStudyFld.label = "Denovo Studies"
    denovoStudyFld.required = False

    transmitted_choices = [('none','none')]
    transmitted_choices.extend([(x,x) for x in vDB.getTransmittedStudies()])
        
    transmittedStudyFld = forms.ChoiceField(transmitted_choices)
    transmittedStudyFld.label = "Transmitted Studies"
    transmittedStudyFld.required = False
    
    VariantTypes = vDB.get_variant_types()
    choices=zip(VariantTypes,VariantTypes)
    variantTypeFld = forms.ChoiceField(choices)
    variantTypeFld.label = "Variant Types"
    variantTypeFld.required = False

    EffectTypes = vDB.get_effect_types()
    choices=zip(EffectTypes,EffectTypes)    
    effectTypeFld = forms.ChoiceField(choices)
    effectTypeFld.label = "Effect Types"
    effectTypeFld.required = False

    
    choices = [('All','All')]
    choices.extend([(x,x) for x in vDB.get_child_types()])
    
    #choices=zip(childTypes,childTypes)    
    childTypeFld = forms.ChoiceField(choices)
    childTypeFld.label = "In Child"
    childTypeFld.required = False

    maxAlleleFreqRareFld = forms.CharField()
    maxAlleleFreqRareFld.label = "Max Allele Frequency"
    maxAlleleFreqRareFld.required = False
    
    minAlleleFreqIntervalFld = forms.CharField()
    minAlleleFreqIntervalFld.label = "Min Allele Frequency"
    minAlleleFreqIntervalFld.required = False
        
    maxAlleleFreqIntervalFld = forms.CharField()
    maxAlleleFreqIntervalFld.label = "Max Allele Frequency"
    maxAlleleFreqIntervalFld.required = False

    familiesFld = forms.CharField(widget=forms.Textarea(attrs={"rows":2,"cols":60}))
    familiesFld.label = "Families"
    familiesFld.required = False

    # check boxes / its a radio box group with  text data entry for some
    
    transmittedChoices = [('all','all'),('ultraRare','ultraRare'),('rare','rare'),('interval','interval')]    
    transmittedTypeFld = forms.ChoiceField(choices=transmittedChoices, widget=forms.RadioSelect())
    transmittedTypeFld.label = "Type:"
    transmittedTypeFld.required = False
    
    
