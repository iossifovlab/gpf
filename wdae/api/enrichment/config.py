'''
Created on Jun 11, 2015

@author: lubo
'''

PHENOTYPES = [
    'autism', 
    'congenital heart disease', 
    'epilepsy', 
    'intelectual disability', 
    'schizophrenia', 
    'unaffected',
]

PRB_TESTS_SPECS = [
    # 0
    {'label': 'prb|Rec LGDs',
     'type': 'rec',
     'inchild': 'prb',
     'effect': 'LGDs'},
    # 1
    {'label': 'prb|LGDs|prb|male,female|Nonsense,Frame-shift,Splice-site',
     'type': 'event',
     'inchild': 'prb', 
     'effect': 'LGDs'},
    # 2
    {'label': 'prb|Male LGDs|prb|male|Nonsense,Frame-shift,Splice-site', 
     'type': 'event',
     'inchild': 'prbM', 
     'effect': 'LGDs'},
    # 3
    {'label': 'prb|Female LGDs|prb|female|Nonsense,Frame-shift,Splice-site', 
     'type': 'event',
     'inchild': 'prbF', 
     'effect': 'LGDs'},
    # 4
    {'label': 'prb|Rec Missense', 
     'type': 'rec',
     'inchild': 'prb',
     'effect': 'missense'},
    # 5
    {'label': 'prb|Missense|prb|male,female|Missense', 
     'type': 'event',
     'inchild': 'prb',
     'effect': 'missense'},
    # 6
    {'label': 'prb|Male Missense|prb|male|Missense', 
     'type': 'event',
     'inchild': 'prbM', 
     'effect': 'missense'},
    # 7
    {'label': 'prb|Female Missense|prb|female|Missense', 
     'type': 'event',
     'inchild': 'prbF', 
     'effect': 'missense'},
    # 8
    {'label': 'prb|Rec Synonymous', 
     'type': 'rec',
     'inchild': 'prb', 
     'effect': 'synonymous'},
    # 9
    {'label': 'prb|Synonymous|prb|male,female|Synonymous', 
     'type': 'event',
     'inchild': 'prb', 
     'effect': 'synonymous'},
    # 10
    {'label': 'prb|Male Synonymous|prb|male|Synonymous', 
     'type': 'event',
     'inchild': 'prbM', 
     'effect': 'synonymous'},
    # 11
    {'label': 'prb|Female Synonymous|prb|female|Synonymous', 
     'type': 'event',
     'inchild': 'prbF', 
     'effect': 'synonymous'},

]

SIB_TESTS_SPECS = [
    # 0
    {'label': 'sib|Rec LGDs', 
     'inchild': 'sib', 
     'effect': 'LGDs'},
    # 1
    {'label': 'sib|LGDs|sib|male,female|Nonsense,Frame-shift,Splice-site', 
     'inchild': 'sib', 
     'effect': 'LGDs'},
    # 2
    {'label': 'sib|Male LGDs|sib|male|Nonsense,Frame-shift,Splice-site', 
     'inchild': 'sibM', 
     'effect': 'LGDs'},
    # 3
    {'label': 'sib|Female LGDs|sib|female|Nonsense,Frame-shift,Splice-site', 
     'inchild': 'sibF', 
     'effect': 'LGDs'},
    # 4
    {'label': 'sib|Rec Missense', 
     'inchild': 'sib', 
     'effect': 'missense'},
    # 5
    {'label': 'sib|Missense|sib|male,female|Missense', 
     'inchild': 'sib', 
     'effect': 'missense'},
    # 6
    {'label': 'sib|Male Missense|sib|male|Missense', 
     'inchild': 'sibM', 
     'effect': 'missense'},
    # 7
    {'label': 'sib|Female Missense|sib|female|Missense', 
     'inchild': 'sibF', 
     'effect': 'missense'},
    # 8
    {'label': 'sib|Rec Synonymous', 
     'inchild': 'sib', 
     'effect': 'synonymous'},
    # 9
    {'label': 'sib|Synonymous|sib|male,female|Synonymous', 
     'inchild': 'sib', 
     'effect': 'synonymous'},
    # 10
    {'label': 'sib|Male Synonymous|sib|male|Synonymous', 
     'inchild': 'sibM', 
     'effect': 'synonymous'},
    # 11
    {'label': 'sib|Female Synonymous|sib|female|Synonymous', 
     'inchild': 'sibF', 
     'effect': 'synonymous'},
]

