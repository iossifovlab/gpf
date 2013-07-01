from django.http import HttpResponse
from django.shortcuts import render
from StringBuilder import *
from django.template import loader, Context, Template
import itertools
from wvdb.forms import VariantForm
from django.http import HttpResponseRedirect
import csv

from DAE import *
from GetVariantsInterface import *

def variants_results(request):
    return render(request, 'variants_results.html')

def mapToFacade(facadeMap, args):
    mappedArgs = {}
       
    for tuple in facadeMap:
        if tuple[1] in args:
            mappedArgs[tuple[0]] = str(args[tuple[1]])
        
    return mappedArgs


def variants_form(request):
    if request.method == 'POST':
        form = VariantForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data

            facadeMap = [('denovoStudies','denovoStudyFld'),                         
                         ('transmittedStudy','transmittedStudyFld'),
                         ('familiesFile','familiesFileFld'),
                         ('familiesList','familiesFld'),  
                         ('geneSym','geneSymbolFld'),
                         ('geneSymFile','geneSymFileFld'),
                         ('geneId','geneIdFld'),
                         ('effectTypes','effectTypeFld'),
                         ('inChild','childTypeFld'),
                         ('variantTypes','variantTypeFld'),
                         ('transmittedType','transmittedTypeFld'),
                         ('popFrequencyMax','maxAlleleFreqRareFld'),
                         ('popFrequencyMin','minAlleleFreqIntervalFld'),
                         ('popFrequencyMax','maxAlleleFreqIntervalFld')
                        ]
            
        
            args = mapToFacade(facadeMap, cd)

            if args['transmittedType']=="ultraRare":
                args['popFrequencyMax']="ultraRare"
                args['popFrequencyMin']="0.0"
            elif args['transmittedType']=="rare":
                if 'popFrequencyMax' not in args:
                    args['popFrequencyMax']="1.0"
                if args['popFrequencyMax']==None or args['popFrequencyMax']=='':
                    args['popFrequencyMax']="1.0"
                
                args['popFrequencyMin']="0.0"
                args['popFrequencyMax']= cd['maxAlleleFreqRareFld']
                
            elif args['transmittedType']=="all":
                args['popFrequencyMin']="-1"
                args['popFrequencyMax']="-1"

            response = HttpResponse(mimetype='text/csv')
            response['Content-Disposition'] = 'attachment; filename=unruly.csv'
            response['Expires'] = '0'

            getVariantsInterface(args,response)
            
            return response
    else:
        form = VariantForm()
        
#        initial={
#        'denovoStudyFld' : "allweandtg",
#        'transmittedStudyFld' : "none",
#        'effectTypesFld' : "LGDs",}        
        
        # i like this way of setting initial values.
        form.fields['denovoStudyFld'].initial = "allWEAndTG"
        form.fields['transmittedStudyFld'].initial = "wig781"
        form.fields['variantTypeFld'].initial = "All"
        form.fields['effectTypeFld'].initial = "LGDs"
        form.fields['transmittedTypeFld'].initial = "ultraRare"
        form.fields['maxAlleleFreqRareFld'].initial = "1.0"
        form.fields['minAlleleFreqIntervalFld'].initial = "0.0"
        form.fields['maxAlleleFreqIntervalFld'].initial = "1.0"

    return render(request, 'variants_form.html', {'form': form})



