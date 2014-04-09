#!/bin/env python

# Jan 17th 2014
# by Ewa


class Grantham:


    aa_long_format = ['Ala', 'Arg', 'Asn', 'Asp', 'Cys', 'Gln', 'Glu', 'Gly', 'His', 'Ile' ,'Leu' ,'Lys' ,'Met' ,'Phe', 'Pro', 'Ser', 'Thr' ,'Trp' ,'Tyr', 'Val']
    aa_short_format = ['A', 'R', 'N', 'D', 'C', 'Q', 'E', 'G', 'H', 'I', 'L', 'K', 'M', 'F', 'P', 'S', 'T', 'W', 'Y', 'V']
    ind = [i for i in xrange(0,20)]
    
    _Indexing = dict(zip(aa_long_format, ind))
    _Indexing.update(dict(zip(aa_short_format, ind)))

    Grantham_Scores =[
        [0],   # Ala, A
        [112,   0],    # Arg, R
        [111,  86,   0], # Asn, N
        [126,  96,  23,   0], # Asp, D
        [195, 180, 139, 154,   0], # Cys, C
        [ 91,  43,  46,  61, 154,   0], # Gln, Q
        [107,  54,  42,  45, 170,  29,   0], # Glu, E
        [ 60, 125,  80,  94, 159,  87,  98,   0], # Gly, G
        [ 86,  29,  68,  81, 174,  24,  40,  98,   0], # His, H
        [ 94,  97, 149, 168, 198, 109, 134, 135,  94,   0], # Ile, I
        [ 96, 102, 153, 172, 198, 113, 138, 138,  99,   5,   0], # Leu, L
        [106,  26,  94, 101, 202,  53,  56, 127,  32, 102, 107,   0], # Lys, K
        [ 84,  91, 142, 160, 196, 101, 126, 127,  87,  10,  15,  95,   0], # Met, M
        [113,  97, 158, 177, 205, 116, 140, 153, 100,  21,  22, 102,  28,   0], # Phe, F
        [ 27, 103,  91, 108, 169,  76,  93,  42,  77,  95,  98, 103,  87, 114,   0], # Pro, P
        [ 99, 110,  46,  65, 112,  68,  80,  56,  89, 142, 145, 121, 135, 155,  74,   0], # Ser, S
        [ 58,  71,  65,  85, 149,  42,  65,  59,  47,  89,  92,  78,  81, 103,  38,  58,   0], # Thr, T 
        [148, 101, 174, 181, 215, 130, 152, 184, 115,  61,  61, 110,  67,  40, 147, 177, 128,   0], # Hrp, W
        [112,  77, 143, 160, 194,  99, 122, 147,  83,  33,  36,  85,  36,  22, 110, 144,  92,  37,   0], # Tyr, Y
        [ 64,  96, 133, 152, 192,  96, 121, 109,  84,  29,  32,  97,  21,  50,  68, 124,  69,  88,  55,   0]] # Val, V
    #    Ala  Arg  Asn  Asp  Cys  Gln  Glu  Gly  His  Ile  Leu  Lys  Met  Phe  Pro  Ser  Thr  Trp  Tyr  Val]
    #    'A', 'R', 'N', 'D', 'C', 'Q', 'E', 'G', 'H', 'I', 'L', 'K', 'M', 'F', 'P', 'S', 'T', 'W', 'Y', 'V'



    def get_score(self, aa1, aa2):
        ''' For example xx.get_score("S", "K") or xx.get_score('Ala','Gln') or xx.get_score('A', 'Gln') '''
        index1 = self._Indexing[aa1]
        index2 = self._Indexing[aa2]
        if index1 < index2:
            score = self.Grantham_Scores[index2][index1]
        else:
            score = self.Grantham_Scores[index1][index2]

        return(score)

    def black_box_grantham(self,bb):
        if bb.effect != "missense":
            return(None)

        return(self.get_score(*bb.aa_change.split('->')))

if __name__ == "__main__":
    from DAE import *
    from VariantAnnotation import annotate_variant

    ra = genomesDB.get_genome()
    gmDB = genomesDB.get_gene_models()
    gr = Grantham()


    print gr.black_box_grantham(annotate_variant(gmDB,ra,loc="1:57489303", var="sub(T->G)")[0])    
    print gr.black_box_grantham(annotate_variant(gmDB,ra,loc="7:100684786", var="sub(T->G)")[0])    
    
