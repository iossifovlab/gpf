BASE_SCORE_CONFIG = '''
[general]
header=id,chrom,starting_pos,scoreValue
noScoreValue=-100
[columns]
chr=chrom
pos_begin=starting_pos
pos_end=starting_pos
score=scoreValue
'''

FULL_SCORE_CONFIG = '''
[sampleScoreName]
header=chrom,starting_pos,ending_pos,reference,alternative,scoreValue,scoreValueTwo
noScoreValue=-101
columns.chr=chrom
columns.pos_begin=starting_pos
columns.pos_end=ending_pos
columns.score=scoreValue,scoreValueTwo
columns.search=reference,alternative
'''
