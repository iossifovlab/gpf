BASE_SCORE_CONFIG = '''
[general]
header=id,chrom,starting_pos,scoreValue
noScoreValue=-100
[columns]
chr=chrom
pos_begin=starting_pos
score=scoreValue
'''

FULL_SCORE_CONFIG = '''
[general]
header=id,chrom,starting_pos,ending_pos,scoreValue,scoreValueAlt
noScoreValue=-101
[columns]
chr=chrom
pos_begin=starting_pos
pos_end=ending_pos
score=scoreValue,scoreValueAlt
'''

SEARCH_SCORE_CONFIG = '''
[general]
header=id,chrom,starting_pos,ending_pos,marker,scoreValue
noScoreValue=-102
[columns]
chr=chrom
pos_begin=starting_pos
pos_end=ending_pos
score=scoreValue
search=marker
'''

MULTI_SCORE_CONFIG = '''
[general]
header=id,chrom,starting_pos,scoreValue
noScoreValue=-103
[columns]
chr=chrom
pos_begin=starting_pos
score=scoreValue
'''
