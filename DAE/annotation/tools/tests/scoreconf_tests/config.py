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

DBNSFP_SCORE_CONFIG = '''
[general]
reference_genome=hg19
noScoreValue=-104
[columns]
chr=chr
pos_begin=pos(1-coor)
pos_end=pos(1-coor)
score=missense
search=ref,alt
'''

FREQ_SCORE_CONFIG = '''
[general]
header=id,chrom,starting_pos,all.altFreq
noScoreValue=-105
[columns]
chr=chrom
pos_begin=starting_pos
score=all.altFreq
'''
