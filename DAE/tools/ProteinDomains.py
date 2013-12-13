#!/bin/env python

# Nov 27th 2013
# written by Ewa

from pylab import *
from collections import defaultdict
import re
import gzip
from DAE import *


gm = genomesDB.get_gene_models()


class Domain:

    def __init__(self, start, stop, domain, desc):
        self.start = start
        self.stop = stop
        self.domain = domain
        self.desc = desc

    def __str__(self):
        desc = "" if self.desc == None else self.desc
        return(str(self.start) + "-" + str(self.stop) + "\t" + self.domain + "\t" + desc)

    def __eq__(self, other):
        return(self.start == other.start and self.stop == other.stop and self.domain == other.domain and self.desc == other.desc)

    def _onclick(self, event):
        print 'button=%d, x=%d, y=%d, xdata=%f, ydata=%f'%(event.button, event.x, event.y, event.xdata, event.ydata)
        print self.domain

    def onclick(self, event):
        self.txt = text(event.xdata, event.ydata, self.domain, fontsize=10)
        fig.canvas.draw()

    def offclick(self, event):
        self.txt.remove()
        fig.canvas.draw()

   

class ProteinDomains:

    gene = None
    Colors = {
        'DOMAIN': 'red',
        'ZN_FING': 'red' ,
        'DNA_BIND': 'red',
        'TRANSIT': 'red',
        'SIGNAL': 'red',
        'TOPO_DOM': 'red',
        'TRANSMEM' : 'orange',
        'INTRAMEM' : 'orange',
        'REPEAT' : 'green',
        'CA_BIND' : 'orange',
        'NP_BIND' : 'orange',
        'REGION' : 'green',
        'COILED' : 'green',
        'MOTIF': 'orange',
        'ACT_SITE': 'red',
        'METAL' : 'orange',
        'BINDING' : 'orange',
        'SITE' : 'orange',
        'NON_STD' : 'green',
        'PEPTIDE': 'green',
        'COMPBIAS' : 'green',
        'CARBOHYD' : 'green',
        'MOD_RES' : 'green',
        'LIPID' : 'green',
        'DISULFID' : 'orange',
        'HELIX': "green",
        }
    _interesting_domains = Colors.keys()

    def set(self, L):
        
        L.sort(key=lambda x: x.start)
        S = [Domain(-1,-1, None, None), L[0]]
        for l in L[1:]:
            for s in S[::-1]:
                if l.start != s.start:
                    S.append(l)
                    break
                if l.stop == s.stop and l.domain == s.domain and l.desc == s.desc:
                    break
        return(S[1:])
                
        

    def protein_position(self, gene_name, loc):

        try:
            gms = gm._geneModels[gene_name]
        except:
            raise Exception("No such gene!")

        #uniprot_len = ???

        for i in gms:
            prot_len = i.CDS_len()/3
        

    def add_variant(self, prot_posB, prot_posE=None):
        if prot_posE == None:
            prot_posE = prot_posB+1
        hlines(y=0.5, xmin = prot_posB, xmax=prot_posE, color="red", linewidth=10)
    

    def __distribute(self, domains, h=0.03):
        
        Height = {}
        keys = sorted(domains, key = lambda x: x.start)
        Height[0.5-h] = [keys[0]]
        
        for i in xrange(1, len(keys)):
            for j in sorted(Height.keys(), reverse=True):
                good_to_go = True 
                for t in Height[j]:
                    if t.stop >= keys[i].start:
                        good_to_go = False
                        break
                if good_to_go == True:
                   Height[j].append(keys[i])
                   break
            if good_to_go == False:
                Height[j-h] = [keys[i]]
                
        return(Height)
            
        
    def draw_gene(self, gene_name, domain_desc=True): ## multiple plots
        
        gene_info = self._D[gene_name]
        if gene_info == []:
            print >>sys.stderr, "No such gene..!"
            return(None)
        
        self.gene = gene_name

        number_of_structures = len(gene_info)
    
        if number_of_structures > 1:
            fig, Axes = subplots(nrows=number_of_structures)
        else:
            fig, ax = subplots(nrows=number_of_structures)
            Axes = [ax]
            
        for i in xrange(0, number_of_structures):

            l = gene_info[i]['AAlength']
            d = float(l)/10
        # fig = figure()
        # ax = fig.add_subplot(1,1,1)
        
            Axes[i].hlines(y=0.5, xmin=1, xmax=l+1, color='k', linewidth=4)
            Axes[i].set_xlim(-d, l+d)
            Axes[i].set_ylim(0, 0.8)
            Axes[i].text(0, 0.6, gene_name, fontsize=20, color="k") #?
            if domain_desc == True:
                h=0.04
            else:
                h=0.02

            h_up =  h/5
            h_down = -h/2
            distr = self.__distribute(self.set(gene_info[i]['domains']), h)
            for y_height,domains in sorted(distr.items(), reverse=True):
                prev_estim_end = -1000
                for dom in domains:
                    dom_len = dom.stop - dom.start + 1
                    Axes[i].hlines(y=y_height, xmin = dom.start, xmax=dom.stop+0.5, color=self.Colors[dom.domain], linewidth=4)
                
                    if domain_desc == True:
                        if prev_estim_end < dom.start:
                            if dom_len > len(dom.domain)*7:
                                Axes[i].text(dom.start + dom_len/2 - len(dom.domain)*4, y_height+h_up, dom.domain, fontsize=10, color='blue')
                                prev_estim_end = dom.stop -1
                            else:
                                Axes[i].text(dom.start, y_height+h_up, dom.domain, fontsize=10, color='blue')
                                prev_estim_end = dom.start + len(dom.domain)*7
                        elif dom_len > len(dom.domain)*8 and dom.start + dom_len/2 - len(dom.domain)*4 > prev_estim_end:
                            Axes[i].text(dom.start + dom_len/2 - len(dom.domain)*4, y_height+h_up, dom.domain, fontsize=10, color='blue')
                            prev_estim_end = dom.stop - 1
                        else:
                            Axes[i].text(dom.start, y_height+h_down, dom.domain, fontsize=10, color='blue')
                            prev_estim_end = -1000
                #fig.canvas.mpl_connect('button_press_event', dom.onclick)
                #fig.canvas.mpl_connect('button_release_event', dom.offclick)
                
        show()
    def _parse_original_file(self, infile, outfile="uniprot_human_FT.dat"):
        file = gzip.open(infile, 'rb')
        res = open(outfile, 'w')
        lines = ''
        human=False
        for line in file:
            if line[:2] in ["GN", "FT", "ID"]:
                line = re.sub('\s\s+', '\t', line)
                lines += line
                continue
            while line[:2] == 'OS':
                ifhomo = re.search('Homo sapiens', line)
                if ifhomo != None:
                    human = True
                    break
                line = file.readline()
                #lines += line
            
            if line[0:2] == '//':
                if human == True:
                    res.write(int(line[2]), int(line[3]))
                lines = ''
                human = False
        
        if human == True:
            res.write(lines)
   
        file.close()
        res.close()


        
        
        

    def _create_dict(self, file="/data/unsafe/autism/genomes/hg19/Uniprot/uniprot_human_FT.dat"):
        self._D = defaultdict(list) 
        f = open(file)
        gene_names = []
        
        while True:
            line = f.readline()
            if not line:
                break 
            line = line[:-1].split("\t")
            if line[0] == 'ID':
                for gene in gene_names:
                    self._D[gene].append({'AAlength':length, 'domains':Dom_list})
                length = int(line[3][:-4])
                gene_names = []
            if line[0] == 'GN':
                #gene_names = []
                while line[0] == 'GN':
                    
                    gn = re.search('Name=([^;]*)', line[1])
                    if gn:
                        gene_name = gn.group(1)
                        gene_names.append(gene_name)
                    
                    gn = re.search('Synonyms=([^;]*)', line[1])
                    if gn:
                        gene_name = gn.group(1)
                        gene_name = gene_name.split(", ")
                        gene_names.extend(gene_name)
                    
                    line = f.readline()
                    line = line[:-1].split("\t")
                Dom_list = []

            if line[0] == "FT":
                if line[1] in self._interesting_domains:
                    if line[2].isdigit() == False or line[3].isdigit() == False:
                        continue
                    if len(line) == 4:
                        Dom_list.append(Domain(int(line[2]), int(line[3]), line[1], None))
                    elif len(line) > 4:
                        Dom_list.append(Domain(int(line[2]), int(line[3]), line[1], line[4]))
        
        for gene in gene_names:
            self._D[gene].append({'AAlength':length, 'domains':Dom_list})
        f.close()
        #print self._D

d = ProteinDomains()
d._create_dict()
#d._parse_original_file("uniprot_sprot.dat.gz")
            

