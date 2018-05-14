#!/usr/bin/python

from __future__ import print_function
import os, sys, optparse, pickle, gzip
from re import search
from subprocess import call, Popen, PIPE

desc = """Program to annotate variants (substitutions & indels) in hg19"""
parser = optparse.OptionParser(version='%prog version 1.2 09/Aug/2012', description=desc)
parser.add_option('-f', help='input file path', action='store', type='string', dest='inputFile')
parser.add_option('-o', help='output file path', action='store', type='string', dest='outputFile')
parser.add_option('-m', help='gene model: refseq or knowngene or ccds', action='store', default = 'refseq', type='string', dest='geneModel')
parser.add_option('-r', help='create splice report', default=False, action='store_true', dest='report')
parser.add_option('-s', help='change 3ss splice site length from 2 to 3', default=2, const=3, action='store_const', dest='ss')
parser.add_option('-d', help='compute the distances to exon boundries for the coding variants', default=False, action='store_true')
parser.add_option('-g', help='gene model file path', type='string', default="/data/unsafe/autism/genomes/hg19/geneModels/refGene.txt.gz", action='store')
parser.add_option('-b', help='capture file path', type='string', default="/data/unsafe/autism/genomes/GATK_ResourceBundle_5777_b37_phiX174/chrAll.fa.fai", action='store')
parser.add_option('-i', help='interactive mode', default=False, dest='interactive', action='store_true')
(opts, args) = parser.parse_args()



goodGeneModels = ["refseq", "ccds", "knowngene"]
if opts.geneModel not in goodGeneModels:
    print("Allowed gene models (-m option) are: refseq, knowngene and ccds")
    parser.print_help()
    sys.exit(-1)


def wczytajZKonsoli(napis, dataType):
    data = raw_input(napis + "\n")
    data = dataType(data)
    return(data)

def czyDozwolone(x, lista):
    if x in lista:
        return(True)
    else:
        return(False)

def czyLiczba(x):
    try:
        int(x)
        return(True)
    except ValueError:
        return(False)

def czySeq(x):
    if x == '':
        return False
    for i in x:
        if i.upper() not in ['A', 'C', 'G', 'T', 'N']:
            return False
    return True


    

chrOk = []
for i in xrange(1,23):
    chrOk.append(str(i))
chrOk.append("X")
chrOk.append("Y")

if opts.interactive == True:

    varType_int = wczytajZKonsoli("Enter the mutation type (D=deletion, I=insertion, S=substitution):", str).upper()
    while czyDozwolone(varType_int, ['S', 'I', 'D']) == False:
        varType_int = wczytajZKonsoli("Incorrect mutation type, please type: D(for deletion) or I (for insertion) or S (for substitution)):", str).upper()
    
    chromosome_int = wczytajZKonsoli("Enter the chromosome number (1-22, X, Y):", str)
    while czyDozwolone(chromosome_int, chrOk) == False:
        chromosome_int = wczytajZKonsoli("Incorrect chromosome number, please type: 1-22 or X or Y:", str)

    position_int = wczytajZKonsoli("Enter the (start) position of the variant:", str)
    while czyLiczba(position_int) == False or int(position_int) < 1:
        position_int = wczytajZKonsoli("Incorect start position of the variant, try again:", str)
    
    if varType_int == "D":
        length_int = wczytajZKonsoli("Enter the length of the deletion:", str)
        while czyLiczba(length_int) == False or int(length_int) < 1:
            length_int = wczytajZKonsoli("Incorrect length of the deletion, try again:", str)
        seq_int = '-'
    else:
        if varType_int == "I":
            seq_int = wczytajZKonsoli("Enter the sequence of the insertion:", str)
            while czySeq(seq_int) == False:
                seq_int = wczytajZKonsoli("Incorrect sequence of the insertion, try again (any combination of: A, C, G, T, N is allowed to use):", str)
            length_int = len(seq_int)
        else:
            seq_int = wczytajZKonsoli("Enter the alternative nucletide:", str)
            while czyDozwolone(seq_int, ['A', 'C', 'G', 'T']) == False:
                seq_int = wczytajZKonsoli("Enter one (!) alternative nucletide: A or C or G or T", str)
            length_int = 1
   
        
else:
    if opts.inputFile == None:
        parser.error('Input filename not given')
    if opts.outputFile == None:
        parser.error('Output filename not given')
    if os.path.exists(opts.inputFile) == False:
        print("The given input file does not exist!")
        sys.exit(-78)

    variantFile = open(opts.inputFile)
    resFile = open(opts.outputFile, 'w')
        
model = opts.geneModel
goodGeneModels.remove(model)
report = opts.report
ssLength = opts.ss
exonBoundries = opts.d
genemodel_file_path = opts.g
if os.path.exists(genemodel_file_path) == False:
    print("The given gene model file does not exist!")
    sys.exit(-79)

ind = genemodel_file_path.rfind("/")
inddot = genemodel_file_path[ind+1:].find(".")

if genemodel_file_path[ind+1:ind + inddot + 1].lower() in goodGeneModels:
    print("Are you sure that a choosen model: " +  model + " is compatibile with a given gene model file: " + genemodel_file_path + "? (y or n)")
    answer = raw_input()
    if answer == "n":
        print("Do you want to choose another gene mode? (y or n)")
        answer2 = raw_input()
        if answer2 == "n":
            sys.exit(0)
        else:
            new_model = raw_input("Choose one of: " + goodGeneModels[0] + " or " +  goodGeneModels[1] + "\n")
            if new_model not in goodGeneModels:
                print("Wrong model name")
                sys.exit(-18)
            else:
                model = new_model
                
call("cp " + genemodel_file_path + " ./", shell=True)
genemodel_file_path = genemodel_file_path[ind+1:]    

if report == True:
    reportFile = open("splice_report.txt", 'w')



stopCodons = ['TAG', 'TAA', 'TGA']

CodonsAa = {'Gly' : ['GGG', 'GGA', 'GGT', 'GGC'],
        'Glu' : ['GAG', 'GAA'],
        'Asp' : ['GAT', 'GAC'],
        'Val' : ['GTG', 'GTA', 'GTT', 'GTC'],
        'Ala' : ['GCG', 'GCA', 'GCT', 'GCC'],
        'Arg' : ['AGG', 'AGA', 'CGG', 'CGA', 'CGT', 'CGC'],
        'Ser' : ['AGT', 'AGC', 'TCG', 'TCA', 'TCT', 'TCC'],
        'Lys' : ['AAG', 'AAA'],
        'Asn' : ['AAT', 'AAC'],
        'Met' : ['ATG'],
        'Ile' : ['ATA', 'ATT', 'ATC'],
        'Thr' : ['ACG', 'ACA', 'ACT', 'ACC'],
        'Trp' : ['TGG'],
        'End' : ['TGA', 'TAG', 'TAA'],
        'Cys' : ['TGT', 'TGC'],
        'Tyr' : ['TAT', 'TAC'],
        'Leu' : ['TTG', 'TTA', 'CTG', 'CTA', 'CTT', 'CTC'],
        'Phe' : ['TTT', 'TTC'],
        'Gln' : ['CAG', 'CAA'],
        'His' : ['CAT', 'CAC'],
        'Pro' : ['CCG', 'CCA', 'CCT', 'CCC']}

CodonsAaKeys = CodonsAa.keys()
seq_pickle = "/mnt/wigclust2/data/safe/levy/windel/seqDic_upper.dump"
seq_dic = pickle.load(open(seq_pickle))


Dict_names = {}

if model == "ccds":
    dict_file = gzip.open("/data/unsafe/autism/genomes/hg19/geneModels/ccdsId2Sym.txt.gz")
    dict_file.readline()
    while True:
        line = dict_file.readline()
        if not line:
            break
        line = line.split()
        Dict_names[line[0]] = line[1]

elif model == "knowngene":
    dict_file = gzip.open("/data/unsafe/autism/genomes/hg19/geneModels/kgId2Sym.txt.gz")
    dict_file.readline()
    while True:
        line = dict_file.readline()
        if not line:
            break
        line = line.split()
        Dict_names[line[0]] = line[1]

KnownChr=[]
captureFile = open(opts.b, 'r')
while True:
    l=captureFile.readline()
    if not l:
        break
    l = l.split()
    KnownChr.append(l[0])
captureFile.close()

def createCdsFiles(model, location):
  
    global seq_dic
    if model == "refseq":
        shift = 1
    elif model == "ccds": 
        shift = 1
    else:
        shift = 0
    
    column_chr = str(2 + shift)
    if location[-3:] == ".gz":
        call("gunzip " + location, shell=True)
        location = location[:-3]
    call("sed -n /#/!p " + location + " > temp.txt", shell=True) 
    call("sort -k" + column_chr + "," + column_chr + " temp.txt > draft_genemodel_file.txt", shell = True)
    
    call("rm temp.txt " + location, shell=True)

    gmodel = open("draft_genemodel_file.txt")

    line = gmodel.readline()
    
    line = line.split()
    new_chr = line[1+shift]


    while True:

        chrom = new_chr
        result_file = open(model + "_utr_human_cds_" + chrom + ".txt", 'w')
    
        while new_chr == chrom:

            if model != "knowngene":
                if model == "refseq":
                    gene = line[12]
                else:
                    gene = line[1]
                frame = line[-1].split(',')[:-1]
                
            
                if len(frame[0]) > 1:
                    if frame[0] == '-1':
                        pass
                    else:
                        frame[0] = frame[0][-1]

                # if there is no reading frame - break
                if frame.count('-1') == len(frame):
                    line = gmodel.readline()
                    if not line:
                        break
                    line = line.split()
                    new_chr = line[1+shift]
                    continue
            else:
                gene = line[0]
        
            
            strand = line[2+shift]
            transcription_start = int(line[3+shift])
            transcription_end = line[4+shift]
            cds_start = line[5+shift]
            cds_end = line[6+shift]
            exon_starts = line[8+shift].split(',')[:-1]
            exon_ends = line[9+shift].split(',')[:-1]
            
        
            # if non-protein coding 
            if cds_start == cds_end:
                line = gmodel.readline()
                if not line:
                    break
                line = line.split()
                new_chr = line[1+shift]
                continue

            # if an exon ends before cds starts - to remove
            for i in xrange(0, len(exon_ends)):
                if int(cds_start) > int(exon_ends[0]):
                    exon_starts.remove(exon_starts[0])
                    exon_ends.remove(exon_ends[0])
                    if model != "knowngene":
                        frame.remove(frame[0])
                else:
                    break

            # if an exon starts before cds starts - to cut
            if int(cds_start) > int(exon_starts[0]):
                exon_starts[0] = str(int(cds_start))

            # if an exon starts after cds ends - to remove
            for i in xrange(len(exon_starts)-1,-1, -1):
                if int(exon_starts[-1]) > int(cds_end):
                    exon_starts.pop()
                    exon_ends.pop()
                    if model != "knowngene":
                        frame.pop()
                else:
                    break

            # if an exon ends after cds ends - to cut
            if int(cds_end) < int(exon_ends[-1]):
                exon_ends[-1] = cds_end



            l = len(exon_starts)
        
            result_file.write(">" + gene + "\t" + chrom + "\t" + strand + "\t" + str(transcription_start + 1) + "\t" + transcription_end + "\n")

            if model != "knowngene":
                for i in xrange(0, l):
                    result_file.write(str(int(exon_starts[i])+1) + "\t" + exon_ends[i] + "\t" + frame[i] + "\t" + seq_dic[chrom][int(exon_starts[i]):int(exon_ends[i])]  + "\n" )       

            else:
                Frame = [0]
                if strand == "+":
                    for e in xrange(0, l):
                        fr = (Frame[e] + int(exon_ends[e]) - int(exon_starts[e]))%3
                        Frame.append(fr)
                    Frame = Frame[:-1]
                else:
                    for e in xrange(0, l):
                        fr = (Frame[e] + int(exon_ends[l - 1 - e]) - int(exon_starts[l - 1 - e]))%3
                        Frame.append(fr)
                    Frame = Frame[:-1]
                    Frame.reverse()
                            
        
                for i in xrange(0, l):
                    result_file.write(str(int(exon_starts[i])+1) + "\t" + exon_ends[i] + "\t" + str(Frame[i]) + "\t" + seq_dic[chrom][int(exon_starts[i]):int(exon_ends[i])] + "\n" )

            line = gmodel.readline()
            if not line:
                break
            line = line.split()
            new_chr = line[1+shift]
      

        result_file.close()
    
        if line == "":
            break



    gmodel.close()

    call("rm draft_genemodel_file.txt", shell=True)



def reverse(nts):
    nts = nts.upper()
    reversed = ''
    for nt in nts:
        if nt == "A":
            reversed += "T"
        elif nt == "T":
            reversed += "A"
        elif nt == "G":
            reversed += "C"
        elif nt == "C":
            reversed += "G"
        elif nt == "N":
            reversed += "N"
        else:
            print(("Invalid nucleotide: ", nt))
            sys.exit(-23)
    return(reversed)

def reverseReport(string):
    string = string.upper()
    reversed = ''
    for s in string:
        if s == "A":
            reversed += "T"
        elif s == "T":
            reversed += "A"
        elif s == "G":
            reversed += "C"
        elif s == "C":
            reversed += "G"
        elif s == ":":
            reversed += ":"
        elif s == ".":
            reversed += "."
        elif s == "(":
            reversed += ")"
        elif s == ")":
            reversed += "("
        else:
            print(("upps, error has occured!", string))
            sys.exit(-10)
    return(reversed)

def changeGeneName(oldName):

    global Dict_names
    
    try:
        return(">" + Dict_names[oldName[1:]])
    except:
        return(oldName)
                

def checkIfIntron(chrom, pos, length, type):
    global model
    global KnownChr
    
    try:
        cdsFile = open(model + "_utr_human_cds_chr" + chrom + ".txt")
    except:
        if chrom in KnownChr:
            return("intergenic","intergenic", "intergenic","intergenic")
        else:
            return("unk_chr", "unk_chr","unk_chr","unk_chr",)

    
    allIntrons = []
    allSplice = []
    allCds = []
    allUtrs = []
    cdsLine = cdsFile.readline()
    
    lineWseq = 3
    
    while True:
        if not cdsLine:
            break
        if cdsLine[0] == ">":
            cdssplt = cdsLine.split()
            newSet = [cdssplt]
            strand = cdssplt[2]
       
            trStart = cdssplt[3]
            trEnd = cdssplt[4]
            
            cdsLine = cdsFile.readline()
            down = 0
            up = 0
            sum = 0
            point = 0
            howManyIntrons = -1
            whichIntron = 0
            found = False
            foundCoding = False
            needNextLine = 0
            codingVariants = []
            c = [-1, -1, -1]
            codon = "" 
            while cdsLine[0] != ">":
                howManyIntrons += 1
                
                cdsLine = cdsLine.split()
               
        
                prevCdsSeq = cdsLine[lineWseq]
                up = int(cdsLine[0])
                
                if down != 0:
                    if (pos < up and pos > down) or (pos + length - 1 < up and pos + length - 1 > down):
                        #print(down, up, pos, strand)
                        found = True
                        point = sum
                        whichIntron = howManyIntrons
                        intronLength = up-down-1
                        
                        if length <= 1:
                            if pos-down <= up-pos:
                                distance = pos - down
                                if strand == "+":
                                    indelside = "5'"
                                else:
                                    indelside = "3'"
                            else:
                                distance = up - pos
                                if strand == "+":
                                    indelside = "3'"
                                else:
                                    indelside = "5'"
                            
                        else:
                            #length>1
                            if pos-down <= up-pos-length:
                                distance = pos-down
                                if strand == "+":
                                    indelside = "5'"
                                else:
                                    indelside = "3'"
                            else:
                                distance = up-pos-length+1
                                if strand == "+":
                                    indelside = "3'"
                                else:
                                    indelside = "5'"

                else:
                    cdsStart = up

                down = int(cdsLine[1])
                
                # check if coding
                if needNextLine != 0:
                    if strand == "+":
                        if needNextLine == 1:
                            c[2] = cdsLine[lineWseq][0]
                        else:
                            c[1] = cdsLine[lineWseq][0]
                            c[2] = cdsLine[lineWseq][1]
                    else:
                        if needNextLine == 1:
                            c[0] = cdsLine[lineWseq][0]
                        else:
                            c[1] = cdsLine[lineWseq][0]
                            c[0] = cdsLine[lineWseq][1]
                    codon = reverse(c[0] + c[1] + c[2])
                    
                
                needNextLine = 0
            
                if (pos >= up and pos <= down) or (pos + length - 1 >= up and pos + length - 1 <= down):
                    foundCoding = True
                    for l in xrange(0, length):
                        if pos + l >= up and pos + l <= down:
                            codingVariants.append((pos+l, l))
                            

                    minPosCod = codingVariants[0][0]
                    maxPosCod = codingVariants[-1][0]
                    deletionLength = len(codingVariants)

                    downDiff = minPosCod-up
                    upDiff = down-maxPosCod
                    
                    if strand == "+":
                        minL = codingVariants[0][1]
                        minimalnyAaPos = sum + pos - up + minL + 1
                        maksymalnyAaPos = sum + pos -up + codingVariants[-1][1] + 1
                        
                        frame = (int(cdsLine[2]) + pos + minL - up)%3
                        howFar = pos + minL - up
                        
                        if howFar - frame < 0:
                            if howFar - frame == -1:
                                
                                c[0] = prevCdsSeq[-1]
                                c[1] = cdsLine[lineWseq][0]
                                c[2] = cdsLine[lineWseq][1]
                               
                            elif howFar - frame == -2:
                                c[0] = prevCdsSeq[-2:-1]
                                c[1] = prevCdsSeq[-1]
                                c[2] = cdsLine[lineWseq][0]
                                
                            else:
                                print(("Bad howFar: ", howFar))
                                sys.exit(-17)
                        
                        elif pos + minL - frame + 2 > down:
                            if pos + minL - frame + 2 - down == 1:
                                needNextLine = 1
                                c[0] = cdsLine[lineWseq][-2:-1]
                                c[1] = cdsLine[lineWseq][-1]
                            elif pos + minL - frame + 2 - down == 2:
                                needNextLine = 2
                                c[0] = cdsLine[lineWseq][-1]
                            else:
                                print(("Bad howFarUp: ", pos + minL -frame + 2 - down))
                                sys.exit(-18)
                        else:
                            if frame == 0:
                                c[0] = cdsLine[lineWseq][howFar]
                                c[1] = cdsLine[lineWseq][howFar+1]
                                c[2] = cdsLine[lineWseq][howFar+2]
                            elif frame == 1:
                                c[0] = cdsLine[lineWseq][howFar-1]
                                c[1] = cdsLine[lineWseq][howFar]
                                c[2] = cdsLine[lineWseq][howFar+1]
                            else:
                                c[0] = cdsLine[lineWseq][howFar-2]
                                c[1] = cdsLine[lineWseq][howFar-1]
                                c[2] = cdsLine[lineWseq][howFar]
                                
                        if needNextLine == 0:
                            codon = (c[0] + c[1] + c[2]).upper()
                            
                                
                            
                    else:
                        minL = codingVariants[-1][1]
                        minimalnyAaPos = sum + pos + minL - up + 1
                        maksymalnyAaPos = sum + pos + codingVariants[0][1] - up + 1
                        frame = (down - pos - minL + int(cdsLine[2]))%3 

                        howFar = down - pos - minL
                    
                        if howFar - frame < 0:
                            if howFar - frame == -1:
                                needNextLine = 1
                                c[1] = cdsLine[lineWseq][-1]
                                c[2] = cdsLine[lineWseq][-2:-1]
                            elif howFar - frame == -2:
                                needNextLine = 2
                                c[2] = cdsLine[lineWseq][-1]
                            else:
                                print(("Bad howFar: ", howFar - frame))
                                sys.exit(-19)

                        elif pos + minL - 2 + frame < up:
                            if pos + minL - 2 + frame - up == -1:
                                c[2] = prevCdsSeq[-1]
                                c[1] = cdsLine[lineWseq][0]
                                c[0] = cdsLine[lineWseq][1]
                            elif pos + minL - 2 + frame - up == -2:
                                c[2] = prevCdsSeq[-2:-1]
                                c[1] = prevCdsSeq[-1]
                                c[0] = cdsLine[lineWseq][0]
                            else:
                                print(("Bad howFarDown: ", pos + minL - 2 + frame - up))
                                sys.exit(-19)
                        else:
                            if frame == 0:
                                c[0] = cdsLine[lineWseq][pos+minL-up]
                                c[1] = cdsLine[lineWseq][pos+minL-up-1]
                                c[2] = cdsLine[lineWseq][pos+minL-up-2]
                                
                            elif frame == 1:
                                c[0] = cdsLine[lineWseq][pos+minL-up+1]
                                c[1] = cdsLine[lineWseq][pos+minL-up]
                                c[2] = cdsLine[lineWseq][pos+minL-up-1]
                            else:
                                c[0] = cdsLine[lineWseq][pos+minL-up+2]
                                c[1] = cdsLine[lineWseq][pos+minL-up+1]
                                c[2] = cdsLine[lineWseq][pos+minL-up]

                        if needNextLine == 0:
                            codon = reverse(c[0] + c[1] + c[2])
                        
                               
                                             
               
                sum += len(cdsLine[lineWseq])
                cdsLine = cdsFile.readline()
                if not cdsLine:
                    break

            if sum%3 != 0:
                sum = sum+2
            
            if found == True or foundCoding == True:
                newName = changeGeneName(newSet[0][0])
                newSet[0][0] = newName
                
                if found == True:
                
                    if strand == "+":
                        posLength = str(((point)/3)+1) + "/" + str(sum/3)
                        posIntron = str(whichIntron) + "/" + str(howManyIntrons)
                    else:
                        posLength = str(((sum-point-1)/3)+1) + "/" + str(sum/3)
                        posIntron = str(howManyIntrons - whichIntron + 1) + "/" + str(howManyIntrons)

                    for each in [posIntron, str(distance), indelside, intronLength, posLength]:
                        newSet.append(each)
                    if distance > ssLength:
                        if newSet not in allIntrons:
                            allIntrons.append(newSet)
                    elif distance == 3:
                        if indelside == "3'":
                            if type == "I" and strand == "+":
                                if newSet not in allIntrons:
                                    allIntrons.append(newSet)
                            else:
                                if newSet not in allSplice:
                                    allSplice.append(newSet) 
                        else:
                            if newSet not in allIntrons:
                                allIntrons.append(newSet) 
                    elif distance == 2:
                        if type == "I":
                            #if (strand == "-" and indelside == "5'"):
                            if (strand == "+" and indelside == "3'") or (ssLength == 2 and strand == "-" and indelside == "5'"):
                                if newSet not in allIntrons:
                                    allIntrons.append(newSet)
                            else:
                                if newSet not in allSplice:
                                    allSplice.append(newSet)
                        else:
                            if newSet not in allSplice:
                                allSplice.append(newSet)
                    elif distance < 1: 
                        if newSet not in allSplice: 
                            allSplice.append(newSet)
                        continue 
                    else:
                        if newSet not in allSplice:
                            allSplice.append(newSet)

                        
                #found codingowy?
                if foundCoding == True:
            
                    if strand == "+":
                        if frame != 2:
                            minAA = str((minimalnyAaPos/3)+1) + "/" + str(sum/3)
                        else:
                            minAA = str(minimalnyAaPos/3) + "/" + str(sum/3)
                        maxAA = str((maksymalnyAaPos/3)+1) + "/" + str(sum/3)
                    else:
                        if frame != 0:
                            minAA = str(((sum - minimalnyAaPos - 1)/3)+1) + "/" + str(sum/3)
                        else:
                            minAA = str(((sum - minimalnyAaPos)/3)+1) + "/" + str(sum/3)
                        maxAA = str(((sum - maksymalnyAaPos - 1)/3)+1) + "/" + str(sum/3)
                    #print(newSet[0][0][1:], strand, minPosCod, maxPosCod, minAA, maxAA,codon, frame, deletionLength, str(downDiff), str(upDiff))
                    newRecord = [newSet[0][0][1:], strand, minPosCod, maxPosCod, minAA, maxAA, codon, frame, deletionLength, str(downDiff), str(upDiff)]
    
                    #print (chr, pos, newRecord, frame)
                    if newRecord not in allCds:
                        allCds.append(newRecord)

            else:
                # found == False and foundCoding == False
                if model != "ccds":
                    utr_res = checkIfUtr(newSet[0][0][1:], strand, int(trStart), cdsStart-1, down+1, int(trEnd), pos, length)
                    if utr_res != None:
                        allUtrs.append(utr_res)
                        
                    
    cdsFile.close()
    return(allIntrons, allSplice, allCds, allUtrs)

def checkIfUtr(gene, plusminus, ts, cs, ce, te, pos, length):

    stop = pos + length - 1
    
    if length == 1:
        if (pos >= ts and pos <= cs):
            dist = cs - pos + 1
            gene = changeGeneName(gene)
            if plusminus == "+":
                return([gene + ":5'UTR", dist])
            else:
                return([gene + ":3'UTR", dist])

        elif (pos >= ce and pos <= te):
            dist = pos - ce + 1
            gene = changeGeneName(gene)
            if plusminus == "+":
                return([gene + ":3'UTR", dist])
            else:
                return([gene + ":5'UTR", dist])

    else:
        # length>1 # & only deletion!
        if (stop >= ts and stop <= cs):
            dist = cs - stop + 1
            gene = changeGeneName(gene)
            if plusminus == "+":
                return([gene + ":5'UTR", dist])
            else:
                return([gene + ":3'UTR", dist])
        elif (pos >= ce and pos <= te):
            dist = pos - ce + 1
            gene = changeGeneName(gene)
            if plusminus == "+":
                return([gene + ":3'UTR", dist])
            else:
                return([gene + ":5'UTR", dist])

            
    return(None)


def checkNewStopCodonIndels(indelSeq, uniqueList):

    global stopCodons

    newStop = []
    
    
    for row in uniqueList:
        if row[0] == '+' and row[1] != 0:
            refcod = row[2]
            if row[1] == 2:
                codonleft = refcod[0:2] + indelSeq[0]
                codonright = indelSeq[-2:] + refcod[2]
            else:
                codonleft = refcod[0:1] + indelSeq[0:2]
                codonright = indelSeq[-1] + refcod[1:]
            if codonleft.upper() in stopCodons or codonright.upper() in stopCodons:
                newStop.append("yes")
            else:
                newStop.append("no")
            
                
        elif row[0] == '-' and row[1] != 2:
            refcod = row[2]
            if row[2] == 0:
                codonleft = refcod[0] + reverse(indelSeq[:-3:-1])
                codonright = reverse(indelSeq[0]) + refcod[1:]
            else:
                codonleft = refcod[0:2] +  reverse(indelSeq[-1])
                codonright = reverse(indelSeq[1::-1]) + refcod[2]


            if (codonleft.upper() in stopCodons) or (codonright.upper() in stopCodons):
                newStop.append("yes")
            else:
               newStop.append("no")
        else:
            newStop.append("no")
            

    return(newStop)

def checkNewStopCodonDel(list, delStart, delStop):
   
    global stopCodons
    ifStop = None

    if list[1] == '+':
        if list[2] == 0:
            ifStop = False
        elif list[2] == 1:
            codon = list[3][0]
            codon += pos2seq(chr, delStop+1, delStop+2)
            if codon.upper() in stopCodons:
                ifStop = True
            else:
                ifStop = False
        else:
            codon = list[3][:2]
            codon += pos2seq(chr, delStop+1, delStop+1)
            if codon.upper() in stopCodons:
                ifStop = True
            else:
                ifStop = False
    else:
        # strand == "-"
        if list[2] == 0:
            ifStop = False
        elif list[2] == 1:
           codon = list[3][0]
           codon += reverse(pos2seq(chr, delStart-2, delStart-1)[::-1])
           if codon.upper() in stopCodons:
                ifStop = True
           else:
                ifStop = False
        else:
           codon = list[3][:2]
           codon += reverse(pos2seq(chr, delStart-1, delStart-1))
           if codon.upper() in stopCodons:
                ifStop = True
           else:
                ifStop = False
    return(ifStop)



def mutationType(aaref, aaalt):
    if aaref == aaalt and aaref != "?":
        return("synonymous")
    elif aaalt == 'End':
        return("nonsense")
    elif aaref == "?" or aaalt == "?":
        return("unknown")
    elif aaref == 'End' and aaalt != 'End':
        return("no_end")
    else:
        return("missense")



def pos2seq(chr, startReport, stopReport):

    global seq_dic
    global KnownChr
    try:
        word = seq_dic["chr" + str(chr)][startReport-1:stopReport]
        return(word)
    except:
        if chr in KnownChr:
            return("intergenic")
        else:
            return("no_chromosome")


        
def completeReport(type, pos, seq, length, word, strand, startRep, stopRep, spliceStart):

    if type == "S":
        
        if strand == "+":
            leftDot = spliceStart-startRep
            rightDot = spliceStart-startRep+2
            word = word[:leftDot] + ":" + word[leftDot:rightDot] + ":" + word[rightDot:]
            if pos < spliceStart:
                x = -1
            else:
                x = 0
            word = word[:pos-startRep+1+x] + "(" + word[pos-startRep+1+x] + "->" + seq + ")" + word[pos-startRep+2+x:]
        else:
            word = reverse(word[::-1])
            leftDot = stopRep - spliceStart - 1
            rightDot = stopRep - spliceStart + 1
            word = word[:leftDot] + ":" + word[leftDot:rightDot] + ":" + word[rightDot:]
            if pos > spliceStart + 1:
                x = -1
            else:
                x = 0
            word = word[:stopRep-pos+1+x] + "(" + word[stopRep-pos+1+x] + "->" + reverse(seq) + ")" + word[stopRep-pos+2+x:]
            
    elif type == "D":
        
        leftDot = spliceStart-startRep
        rightDot = spliceStart-startRep+2
        word = word[:leftDot] + ":" + word[leftDot:rightDot] + ":" + word[rightDot:]
        
        if pos >= spliceStart:
            x = 1
            if pos > spliceStart + 1:
                x += 1
        else:
            x = 0
        if pos + length  > spliceStart + 2:
            y = 1
        elif pos + length < spliceStart + 1:
            y = -1
        else:
            y = 0
         
        word = word[:pos-startRep+x] + "(" + word[pos-startRep+x : pos-startRep+length + 1 + y] + ")" + word[pos-startRep+length+ 1 + y:]
            
        if strand == "-":
            word = reverseReport(word[::-1])
            
    elif type == "I":

        
        leftDot = spliceStart-startRep
        rightDot = spliceStart-startRep+2
        word = word[:leftDot] + ":" + word[leftDot:rightDot] + ":" + word[rightDot:]
        if pos < spliceStart:
            x = -1
        elif pos > spliceStart + 1:
            x = 1
        else:
            x = 0

        word = word[:pos-startRep+1+x] + "(" + seq + ")" + word[pos-startRep+1+x:] 
        if strand == "-":
            word = reverseReport(word[::-1])
        
    else:
        print("wrong mutation type (D/I/S)")
        sys.exit(-1)

    return(word)

def findSplicePos(spliceOutput, mutPos, length):

    # length for Indel = 1!

    strand = spliceOutput[0][2]
    ss = spliceOutput[3]
    dist = int(spliceOutput[2])
   
    if (strand == "+" and ss == "5'") or (strand == "-" and ss == "3'"):
        if dist <= 3:
            splicePos = (mutPos-dist+1, mutPos-dist+2)
        else:
            print(("Wrong splice position: ", spliceOutput))
            sys.exit(-3)
            
    elif (strand == "+" and ss == "3'") or (strand == "-" and ss == "5'"):
        if dist <= 3:
            splicePos = (mutPos+length+dist-3, mutPos+length+dist-2)
        else:
            print(("Wrong splice position: ", spliceOutput))
            sys.exit(-3)

    else:
        print(("Something is wrong with a splice output: ", spliceOutput))
        sys.exit(-3)
    #print splicePos
    return(splicePos)

def cod2aa(codon):
    global CodonsAa
    global CodonsAaKeys

    
    codon=codon.upper()
    if len(codon) != 3:
        return("?")
        
    good = ['A', 'C', 'T', 'G', 'N']
    for i in codon:
        if i not in good:
            print("Codon can only contain: A, G, C, T, N letters, this codon is: " + codon)
            sys.exit(-21)
        if i == "N":
            return("?")

    for key in CodonsAaKeys:
        if codon in CodonsAa[key]:
            return(key)
        
    return(None)

def unknownChr(type, interactive, i):
    global resFile
    
    if i == 1:
        text = "unk_chr"
    else:
        text = "intergenic"
    
    if type == "D":
        if interactive == False:
            resFile.write(chr + "\t" + str(indelStart) + "\t" + type + "\t" + str(length) + "\t" + text + "\t" + text + "\t" + text + "\n")
        else:
            print(chr + "\t" + str(indelStart) + "\t" + type + "\t" + str(length) + "\t" + text + "\t" + text + "\t" + text + "\n" )
            
    else:
        if interactive == False:
            
            resFile.write(chr + "\t" + str(indelStart) + "\t" + type + "\t" + sequence  + "\t" + text + "\t" + text + "\t" + text + "\n")
        else:
            print(chr + "\t" + str(indelStart) + "\t" + type + "\t" + sequence  + "\t" + text + "\t" + text + "\t" + text + "\n")



createCdsFiles(model, genemodel_file_path)

if opts.interactive == False:
    line = variantFile.readline()
    line = line.split()
    resFile.write(line[0] + "\t" + line[1]+"\t"+line[2]+"\tseq/length\t" + "effectType\teffectGene\teffectDetails\n")
        
    
while True:

    if opts.interactive == True:
        chr=chromosome_int
        indelStart=int(position_int)
        type=varType_int
        length=int(length_int)
        sequence=seq_int

    else:
        line = variantFile.readline()
        if not line:
            break
        if line[0] == "#":
            resFile.write("\n")
            continue   
        line = line.split()
        chr = line[0]
        indelStart = int(line[1])
        type = line[2]
        length = int(line[4])
        sequence = line[3]

    coding = None
    worst = None
    frameShiftIntron = None
    frameShiftDeletion = []

    newStopsDel = []
    splice = []
    genes = []
    positionsCoding = []
    positionsIntron = []
    positionsAll = ''
    effects = ''

    if report == True:
        reportMemory = ">" + chr + "\t" + str(indelStart) + "\t" + type + "\t" +  str(length) + "\t" + sequence + "\n"

    # DELETION
    if type == 'D':
        delEnd = indelStart + length - 1
        spliceCod = []
        spliceUniqGene = []
        positionsSplice = []

        intr, splice, cds, utrs = checkIfIntron(chr, indelStart, length, "D")

        if intr == splice == cds == utrs == "unk_chr":
            unknownChr('D', opts.interactive, 1)
            continue
        if intr == splice == cds == utrs == "intergenic":
            unknownChr('D', opts.interactive, 2)
            continue
        
        if splice != []:
            worst = "splice-site"
            if report == True:
                reportFile.write(reportMemory)
            for s in splice:             
                found = False
                spliceGene = s[0][0][1:]
                if spliceGene not in spliceUniqGene:
                    spliceUniqGene.append(spliceGene)
                    #if int(s[2]) < 1:
                     #   spliceCod.append([spliceGene, s[5]])
                    effects += spliceGene + ":splice-site|"
                    positionsSplice.append([s[5]]) 
                else:
                    
                    if int(s[2]) < 1:
                     
                        indeks = spliceUniqGene.index(spliceGene)
                        positionsSplice[indeks].append(s[5])

                if report == True:
                    
                   
                    spliceBegin, spliceEnd = findSplicePos(s, indelStart, length)
                    refContext = pos2seq(chr, indelStart - 6, indelStart + length + 5)
                    if refContext == "no_chromosome":
                        if opts.interactive == False:
                            unknownChr('D', opts.interactive, 1)
                        else:
                            print(chr + "\t" + str(indelStart) + "\t" + type + "\tno such chromosome in the gene model\n")
                            break
                        continue
                    if refContext == "intergenic":
                        if opts.interactive == False:
                            unknownChr('D', opts.interactive, 2)
                        else:
                            print(chr + "\t" + str(indelStart) + "\t" + type + "\tno genes for that chromosome\n")
                            break
                        continue
                    splContx = completeReport("D", indelStart, "", length, refContext, s[0][2], indelStart-6, indelStart + length + 5, spliceBegin)

                    reportFile.write("gene:" + spliceGene + "\tstrand:" + s[0][2] + "\tss:" + s[3] + "\taa_pos:" + s[5] + "\tintron_nu:" + s[1] + "\tintron_length:" + str(s[4]) + "\t" + splContx + "\n" )
                      
            for each in positionsSplice:
                for e in each:
                    positionsAll += e + ";"
                    positionsAll = positionsAll[:-1] + "|"


    
        if cds == []:
            coding = False
          
        else:
            coding = True
            for c in cds:
                genes.append(c[0])
                    
                positionsCoding.append([c[0], c[4], c[9], c[10]])  
                if c[8]%3 == 0:
                   frameShiftDeletion.append('no')  
                   a = c[2]
                   b = c[3]
                   newStopsDel.append(checkNewStopCodonDel([c[4], c[1], c[7], c[6]], a, b))
                else:
                    frameShiftDeletion.append('yes')
                    newStopsDel.append(None)
              
        if coding == True and worst == None:
            if "yes" in frameShiftDeletion:
                worst = "frame-shift"
            else:
                if True in newStopsDel:
                    worst = "no-frame-shift-new-Stop"
                else:
                    worst = "no-frame-shift"
            

        if utrs != [] and worst == None:
            worst = "UTR"
     
        if intr != [] and worst == None:
            worst = "intron"

        if worst == None:
            worst = "intergenic"


        if coding == True:
            uniqYes = []
            uniqNo = []
            uniqNo_new = []
            coding_aa_pos_yes = []
            coding_aa_pos_noNew = []
            coding_aa_pos_no = []
            for fs in xrange(0, len(frameShiftDeletion)):
                if frameShiftDeletion[fs] == "yes":
                    if positionsCoding[fs][0] not in uniqYes:
                        uniqYes.append(positionsCoding[fs][0])
                        effects += positionsCoding[fs][0] + ":frame-shift|"
                        if exonBoundries == True:
                            coding_aa_pos_yes.append([positionsCoding[fs][1], positionsCoding[fs][2], positionsCoding[fs][3]])
                        else:
                            coding_aa_pos_yes.append([positionsCoding[fs][1]])
                    else:
                        indeks = uniqYes.index(positionsCoding[fs][0])
                        if exonBoundries == True:
                            coding_aa_pos_yes[indeks].append(positionsCoding[fs][1])
                            coding_aa_pos_yes[indeks].append(positionsCoding[fs][2])
                            coding_aa_pos_yes[indeks].append(positionsCoding[fs][3])
                        else:
                            coding_aa_pos_yes[indeks].append(positionsCoding[fs][1])
                        
                    
                else:
                    if newStopsDel[fs] == True:
                        if positionsCoding[fs][0] not in uniqNo_new:
                            uniqNo_new.append(positionsCoding[fs][0])
                            effects += positionsCoding[fs][0] + ":no-frame-shift-new-Stop|"
                            if exonBoundries == True:
                                coding_aa_pos_noNew.append([positionsCoding[fs][1], positionsCoding[fs][2], positionsCoding[fs][3]])
                            else:
                                coding_aa_pos_noNew.append([positionsCoding[fs][1]])
                        else:
                           indeks = uniqNo_new.index(positionsCoding[fs][0])
                           if exonBoundries == True:
                               coding_aa_pos_noNew[indeks].append(positionsCoding[fs][1])
                               coding_aa_pos_noNew[indeks].append(positionsCoding[fs][2])
                               coding_aa_pos_noNew[indeks].append(positionsCoding[fs][3])
                           else:
                               coding_aa_pos_noNew[indeks].append(positionsCoding[fs][1]) 
                    else:
                        if positionsCoding[fs][0]  not in uniqNo:
                            uniqNo.append(positionsCoding[fs][0])
                            effects += positionsCoding[fs][0] + ":no-frame-shift|"
                            if exonBoundries == True:
                                coding_aa_pos_no.append([positionsCoding[fs][1], positionsCoding[fs][2], positionsCoding[fs][3]])
                            else:
                                coding_aa_pos_no.append([positionsCoding[fs][1]])
                        else:
                           indeks = uniqNo.index(positionsCoding[fs][0])
                           if exonBoundries == True:
                               coding_aa_pos_no[indeks].append(positionsCoding[fs][1])
                               coding_aa_pos_no[indeks].append(positionsCoding[fs][2])
                               coding_aa_pos_no[indeks].append(positionsCoding[fs][3])
                           else:
                               coding_aa_pos_no[indeks].append(positionsCoding[fs][1])  

           
            
            for each in [coding_aa_pos_yes, coding_aa_pos_noNew, coding_aa_pos_no]:
                for e in each:
                    if exonBoundries == True:
                        for m in xrange(0, len(e), 3):
                            positionsAll += e[m] + "[" + e[m+1] + "," + e[m+2] + "];"
                    else:
                        for m in e:
                            positionsAll += m + ";"
                    positionsAll = positionsAll[:-1] + "|"
            
                
      
        
    elif type == "I":
        # INSERTION
        
        intr, splice, cds, utrs = checkIfIntron(chr, indelStart, 1, "I")
        if intr == splice == cds == utrs == "unk_chr":
            unknownChr('I', opts.interactive, 1)
            continue
        if intr == splice == cds == utrs == "intergenic":
            unknownChr('I', opts.interactive, 2)
            continue
        
        #if output == []:
        if cds == []:
            coding = False

           
        else:
            coding = True
            chosenColumnsCod = []
            for c in cds:
                if c[0] not in genes:
                    genes.append(c[0])
                    if exonBoundries == True:
                        positionsCoding.append([c[4] + "[" + c[9] + "," + c[10] + "]"])
                    else:
                        positionsCoding.append([c[4]])
                else:
                    indeks = genes.index(c[0])
                    if exonBoundries == True:
                        positionsCoding[indeks].append(c[4] + "[" + c[9] + "," + c[10] + "]" )
                    else:
                        positionsCoding[indeks].append(c[4]) 
                   

            # frameshift?
            if len(sequence)%3 == 0:
                frameShiftIntron = False
                worst = "no-frame-shift"
                # new stop codon?
                for cod in cds:
                    chosenColumnsCod.append([c[1], c[7], c[6], c[0]])
                stops = checkNewStopCodonIndels(sequence, chosenColumnsCod)
               
            else:
                frameShiftIntron = True
                worst = "frame-shift"

        #utrs = checkIfUtr(chr, indelStart, 1)
        if utrs != []  and worst == None:
            worst = "UTR"        

        if splice != []:
            worst = "splice-site"
        elif intr != []  and worst == None:
            worst = "intron"

        if worst == None:
            worst = "intergenic"

        
        #effects    

        spliceUniqGene = []
        positionsSplice = []
        if splice != []:
           if report == True:
               reportFile.write(reportMemory)
           for s in splice:
              spliceGene = s[0][0][1:]
              if spliceGene not in spliceUniqGene:
                 spliceUniqGene.append(spliceGene)
                 effects += spliceGene + ":splice-site|"
                 positionsSplice.append([s[5]])
              else:
                 indeks = spliceUniqGene.index(spliceGene)
                 positionsSplice[indeks].append(s[5])

              if report == True:
                  spliceBegin, spliceEnd = findSplicePos(s, indelStart, 1)
                  refContext = pos2seq(chr, indelStart - 6, indelStart + 6)

                  if refContext == "no_chromosome":
                      if opts.interactive == False:
                          unknownChr('I', opts.interactive, 1)
                      else:
                          print(chr + "\t" + str(indelStart) + "\t" + type + "\tno such chromosome in the gene model\n")
                          break
                      continue
                  if refContext == "intergenic":
                      if opts.interactive == False:
                          unknownChr('I', opts.interactive, 2)
                      else:
                          print(chr + "\t" + str(indelStart) + "\t" + type + "\tno genes for that chromosome\n")
                          break
                      continue
                  splContx = completeReport("I", indelStart, sequence, length, refContext, s[0][2], indelStart-6, indelStart+6, spliceBegin)

                  reportFile.write("gene:" + spliceGene+ "\tstrand:" + s[0][2] + "\tss:" + s[3]+ "\taa_pos:" + s[5] + "\tintron_nu:" + s[1] + "\tintron_length:" + str(s[4])+ "\t" + splContx + "\n" )
                 
           for each in positionsSplice:
              for e in each:
                 positionsAll += e + ";"
                 positionsAll = positionsAll[:-1] + "|"
                    

        
        
        if coding == True:
            if frameShiftIntron == True:
                for gene in genes:
                    effects += gene + ":frame-shift|"
             
            else:
                uniq = []
                for cc in xrange(0, len(chosenColumnsCod)):
                    if stops[cc] == "no":
                        napis = chosenColumnsCod[cc][3] + ":no-frame-shift|"
                        if napis not in uniq:
                            uniq.append(napis)
                            effects += napis
                    else:
                        worst = "no-frame-shift-new-stop"
                        napis = chosenColumnsCod[cc][3] + ":no-frame-shift-new-stop|"
                        if napis not in uniq:
                            uniq.append(napis)
                            effects += napis
          

            for hit in positionsCoding:
                for i in hit:
                    positionsAll += i + ";"
                positionsAll = positionsAll[:-1] + "|"


        
    elif type == "S":
        # SNPs
        
        nonPos = []
        misPos = []
        synPos = []
        unkPos = []
        snpPos = indelStart

        refNt = pos2seq(chr, indelStart, indelStart)
    
        if refNt == "no_chromosome":
            if opts.interactive == False:
                unknownChr('S', opts.interactive, 1)
            else:
                print(chr + "\t" + str(indelStart) + "\t" + type + "\tno such chromosome in the gene model\n")
                break
            continue
        if refNt == "intergenic":
            if opts.interactive == False:
                unknownChr('S', opts.interactive, 2)
            else:
                print(chr + "\t" + str(indelStart) + "\t" + type + "\tno genes for that chromosome\n")
                break
            continue
        if refNt == sequence:
            worst = "no-mutation"
            if opts.interactive == False:
                resFile.write(chr + "\t" + str(indelStart) + "\t" + type + "\t" + str(length) + "\t" + worst + "\t" + worst + "\t" + worst + "\n")
            else:
                print(chr + "\t" + str(indelStart) + "\t" + type + "\t" + str(length) + "\t" + worst + "\t" + worst + "\t" + worst + "\n")
                break
            continue
        
        
        intr, splice, cds, utrs = checkIfIntron(chr, indelStart, 1, "S")
        if intr == splice == cds == utrs == "unk_chr":
             unknownChr('S', opts.interactive, 1)
             continue
        if intr == splice == cds == utrs == "intergenic":
            unknownChr('S', opts.interactive, 2)
            continue
            
        spliceUniqGene = []
        positionsSplice = []
        if splice != []:
            worst = "splice-site"
            if report == True:
                reportFile.write(reportMemory)
            for s in splice:
                spliceGene = s[0][0][1:]
                if spliceGene not in spliceUniqGene:
                    spliceUniqGene.append(spliceGene)
                    effects += spliceGene + ":splice-site|"
                    positionsSplice.append([s[5]])
                else:
                    indeks = spliceUniqGene.index(spliceGene)
                    positionsSplice[indeks].append(s[5])

                if report == True:
                    spliceBegin, spliceEnd = findSplicePos(s, indelStart, 1)
                    refContext = pos2seq(chr, indelStart - 6, indelStart + 6)
                    spltContx = completeReport("S", indelStart, sequence, 1, refContext, s[0][2], indelStart-6, indelStart+6, spliceBegin)
                    reportFile.write("gene:" + spliceGene + "\tstrand:" + s[0][2] + "\tss:" + s[3] + "\taa_pos:" + s[5] + "\tintron_nu:" + s[1] + "\tintron_length:" + str(s[4]) + "\t" + spltContx + "\n" )
                                   
            for each in positionsSplice:
                for e in each:
                    positionsAll += e + ";"
                positionsAll = positionsAll[:-1] + "|"
                    
     
                
        
        if cds == []:
            coding = False
            # non-coding

        else:
            # coding
            coding = True
            uniqNon = []
            uniqMis = []
            uniqSyn = []
            uniqUnk = []
            for c in cds:
                strand = c[1]
                frame = c[7]
                refaa = cod2aa(c[6])
                downDiff = c[9]
                upDiff = c[10]
                if strand == "+":
                    altcodon = c[6][:frame] + sequence + c[6][frame+1:]
                else:
                    altcodon = c[6][:frame] + reverse(sequence) + c[6][frame+1:]
                altaa = cod2aa(altcodon)
                mutType = mutationType(refaa, altaa)
            
                if mutType == "nonsense":
                    worst = "nonsense"
                    if c[0] not in uniqNon:
                        uniqNon.append(c[0])
                        nonPos.append([[c[0], refaa, altaa, c[4], downDiff, upDiff]])
                    else:
                        indeks = uniqNon.index(c[0])
                        nonPos[indeks].append([c[0], refaa, altaa, c[4], downDiff, upDiff])
                elif mutType == "missense":
                    if worst == None or worst == "synonymous":
                        worst = "missense"
                    if c[0] not in uniqMis:
                        uniqMis.append(c[0])
                        misPos.append([[c[0], refaa, altaa, c[4], downDiff, upDiff]])
                    else:
                        indeks = uniqMis.index(c[0])
                        misPos[indeks].append([c[0], refaa, altaa, c[4], downDiff, upDiff])
                        
                    
                elif mutType == "synonymous":
                    if worst == None or worst == "unknown":
                        worst = "synonymous"
                    if c[0] not in uniqSyn:
                        uniqSyn.append(c[0])
                        synPos.append([[c[0], c[4], downDiff, upDiff]]) 
                    else:
                        indeks = uniqSyn.index(c[0])
                        synPos[indeks].append([c[0], c[4], downDiff, upDiff])

                elif mutType == "unknown":
                    if worst == None:
                        worst = "unknown"
                    if c[0] not in uniqUnk:
                        uniqUnk.append(c[0])
                        unkPos.append([[c[0], refaa, altaa, c[4], downDiff, upDiff]])
                    else:
                        indeks = uniqUnk.index(c[0])
                        unkPos[indeks].append([c[0], refaa, altaa, c[4], downDiff, upDiff])
                        
            nonPos.append("nonsense")
            misPos.append("missense")
            synPos.append("synonymous")
            unkPos.append("unknown")
            for list in [nonPos, misPos, synPos, unkPos]:
                word = list[-1]
                for each in list[:-1]:
                    effects += each[0][0] + ":" + word + "|"
                    for e in each:
                        if exonBoundries == True:
                            if word == "synonymous":
                                positionsAll += e[1] + "[" + e[-2] + "," + e[-1] +  "];" ##-1->1 
                            else:
                                positionsAll += e[3] + "(" + e[1] + "->" + e[2] + ")[" + e[-2] + "," + e[-1] +  "];"  # -1->3
                        else:
                            if word == "synonymous":
                                positionsAll += e[1] + ";" ##-1->1 
                            else:
                                positionsAll += e[3] + "(" + e[1] + "->" + e[2] + ");"  # -1->3
                    positionsAll = positionsAll[:-1] + "|"


        #utrs = checkIfUtr(chr, indelStart, 1)
        if utrs != []  and worst == None:
            worst = "UTR"        
            
        if intr != []  and worst == None:
            worst = "intron"

        if worst == None:
            worst = "intergenic"

      
    else:
        print(("Error in mutation type!: ", type))
        sys.exit(0)
        
   
    
    if utrs != []:
        uniq = []
        distUtr = []
        for utr in utrs:
            if utr[0] not in uniq:
                uniq.append(utr[0])
                effects += utr[0] + "|"
                distUtr.append([utr[1]])
            else:
                indeks = uniq.index(utr[0])
                distUtr[indeks].append(utr[1])
        for distances in distUtr:
            for d in distances:
               positionsAll += "[" + str(d) + "];"
            positionsAll = positionsAll[:-1] + "|" 

   
    if intr != []:
        uniq = []
        for i in intr:
            if i[0][0] not in uniq:
                uniq.append(i[0][0])
                effects += i[0][0][1:] + ":intron|"
                positionsIntron.append([i[1] + "[" + i[2] + "]"])
            else:
                indeks = uniq.index(i[0][0])
                positionsIntron[indeks].append(i[1] + "[" + i[2] + "]")
            
        for hit in positionsIntron:
            for i in hit:
                positionsAll += i + ";"
            positionsAll = positionsAll[:-1] + "|"        
                
            
            
    if effects != "":
        effects = effects[:-1]
    else:
        effects = "intergenic"
            

    if positionsAll != '':
        positionsAll = positionsAll[:-1]
    else:
        positionsAll = "integrenic"
       
    if type == "D":
        if opts.interactive == False:
            resFile.write(chr + "\t" + str(indelStart) + "\t" + type + "\t" + str(length) + "\t" + worst + "\t" + effects + "\t" + positionsAll + "\n")
        else:
            print(chr + "\t" + str(indelStart) + "\t" + type + "\t" + str(length) + "\t" + worst + "\t" + effects + "\t" + positionsAll + "\n")
            break
    else:
        if opts.interactive == False:
            resFile.write(chr + "\t" + str(indelStart) + "\t" + type + "\t" + sequence + "\t" + worst + "\t" + effects + "\t" + positionsAll + "\n")
        else:
            print(chr + "\t" + str(indelStart) + "\t" + type + "\t" + sequence + "\t" + worst + "\t" + effects + "\t" + positionsAll + "\n")
            break

if opts.interactive == False:
    variantFile.close()
    resFile.close()

call("rm " + model + "_utr_human_cds_*", shell=True)

if report == True:
    print("Splice report was saved as: splice_report.txt")
    reportFile.close()


