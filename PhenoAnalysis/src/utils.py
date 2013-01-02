'''
Created on Nov 7, 2012

@author: Tony
'''

import re

def findWords(value):
    words = {}
    
#    dataType = getDataType(value)         
#    
#    if dataType == 'empty':
#        return words.keys()
#
#    if dataType == 'numeric':
#        return words.keys()
#        
#    if value == None:
#        return words.keys()
            
    value = value.strip()
                                              
    if len(value) == 0:
        return words.keys() 
                                                                
    # uncomment to filter values
    #if is_garbage(value):
    #    return words.keys()         
    
    if value.find("\r\n")>0:
        value = value.replace("\r\n", ' ')
    if value.find("\n")>0:                
        value = value.replace("\n", ' ')
    if value.find("\r")>0:                
        value = value.replace("\r", ' ')
       
    value = value.lower()
    
    # '-','\'',
    subs = ['\t',',',';',':','.','!','"','(',')','[',']','`']
    
    for ch in subs:              
        value = value.replace(ch, ' ')
                    
    data = value.split(' ')
    for word in data:
        
        if word == None:
            break        
        
        word = word.strip()
        
        if len(word) == 0:
            break
        
        words[word]=0
         
        #if len(word)>0:                
        #    if "_" in word:             
        #        data2 = value.split('.')
        #        for word2 in data2:
        #            words[word2]=0                                            
        #    else:
        #        words[word]=0
        
    
    return words.keys()   


def is_boolean(s):
        
    if (s=='true') or (s=='false'): 
        return True

    if (s=='yes') or (s=='no') or (s=='not-sure'): 
        return True

    return False

def is_float(s):
    match = re.match('^(?=.+)(?:[1-9]\d*|0)?(?:\.\d+)?$', s)
    if match:
        return True
    else:
        return False

def is_integer(s):
    match = re.match('^[0-9]+$', s)
    if match:
        return True
    else:
        return False

def is_number(s):
           
    try:
        float(s) # for int, long and float
    except ValueError:
        try:
            complex(s) # for complex
        except ValueError:
            return False

    return True

def is_date(s):

    match = re.match('^[0-9]+/[0-9]+/[0-9]+$', s)
    if match:
        return True
    
    match = re.match('^[0-9]{4}-[0-9]{2}$', s)
    if match:
        return True

    #match = re.match('[0-9]{1}:[0-9]{2}', s)
    #if match:
    #    return True

    match = re.match('^([0-9]+)(:|-)([0-9]+)$', s)
    if match:
        return True

    match = re.match('^[0-9]{2}:[0-9]{2}:[0-9]{2}$', s)
    if match:
        return True

    return False


def getDataType(s):

    
    if s == None:
        return 'empty'    
    
    if len(s) == 0:
        return 'empty'
    
    #if is_number(s):
    #    return 'numeric'

    if is_integer(s):
        return 'numeric'

    if is_float(s):
        return 'numeric'
            
    #if is_boolean(s):
    #    return 'boolean'
            
    #if is_date(s):
    #    #return 'date'
    #    return 'string'

    return 'string'

def is_garbage(s):

    if s == "-":
        return True
    
    if s=="[phi suspected]":
        return True
    
    match = re.match('^NDAR*', s)
    if match:
        return True

    match = re.match('([0-9]+)(.)([0-9]+)(-|;)([0-9]+)(.)([0-9]+)', s)
    if match:
        return True
    
    match = re.search('([0-9]{5,})(.)(mo|fa|[pxs][0-9])',s)
    if match:        
        return True
    
    return False
