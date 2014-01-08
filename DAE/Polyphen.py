#!/bin/env python
# Jan 8th 2013
# by Ewa

import sqlite3
import sys
from collections import namedtuple

class Polyphen:
    
    def connect_to_db(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.c = self.conn.cursor()

    def get_variant(self, chr, pos, ref, alt):

        v = self.c.execute("SELECT chrom||':'||chrpos AS chrpos,gene,nt1,nt2,pos,aa1,aa2,hdiv_prediction,hdiv_prob,hvar_prediction,hvar_prob FROM features JOIN scores USING(id) WHERE chrom='" + chr + "' AND chrpos='" + str(pos) + "' AND nt1='" + ref + "' AND nt2='" + alt + "' ORDER BY hdiv_prob DESC LIMIT 1;")
        v = v.fetchone()
        if v != None:
            v = self._t(loc=str(v[0]),gene=str(v[1]),ref=str(v[2]), alt=str(v[3]), prot_pos=v[4], aa_ref=str(v[5]), aa_alt=str(v[6]), hdiv_pred=str(v[7]), hdiv_prob=v[8], hvar_pred=str(v[9]), hvar_prob=v[10]) 
        return(v)


def load_polyphen(file="/data/unsafe/autism/genomes/hg19/Polyphen2/polyphen-2.2.2-whess-2011_12.sqlite"):
    p = Polyphen()
    p.connect_to_db(file)
    p._t = namedtuple("pp2", 'loc gene ref alt prot_pos aa_ref aa_alt hdiv_pred hdiv_prob hvar_pred hvar_prob')
    return(p)


