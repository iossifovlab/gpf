#!/data/software/local/bin/python

import string
import sys
import copy
import re

class objectgraph:

    def __init__(self,fname):
        self.req = {}
        self.params = {}
        self.objectsByKey = {}
        self.objectsByType = {}
        self.baseDir = ""

        self.loadFile(fname)
        self._generateOLinks()
  
    def _generateOLinks(self):
        for o in self.objectsByKey.values():
            o.depsO = [self.objectsByKey[x] for x in o.deps]
            o.parentsO= [self.objectsByKey[x] for x in o.parents]
        
    def fillHash(self, line, h):
        p = re.compile('^(.*)=(.*)$')
        m = p.match(line)
        if m:
            h[m.group()[:m.group().index("=")]] = m.group()[m.group().index("=")+1:]

    def printH(self, h):
        for nn in h.keys():
            print nn+"="+h[nn]

        
    def addObject(self, ob):
        key = ob.type+":"+ob.name

        if key in self.objectsByKey:
                   print "The object " + key + " is already added\n";
                   raise
        self.objectsByKey[key] = ob;
        if ob.type in self.objectsByType:
            self.objectsByType[ob.type][ob.name] = ob
        else:
            self.objectsByType[ob.type] = {}
            self.objectsByType[ob.type][ob.name] = ob

    def objDir(self, o):
        patt = self.params["obj.dir.pattern"]
        NNN = o.NNN
        nodeObjDir=patt.replace("${NNN}", str(NNN))
        return nodeObjDir+"/"+o.type+"/"+o.name

    def writeObjectGraph(self,outFile):
        f=open(self.baseDir + "/" + outFile, "w") 
        f.write("OBJECT_GRAPH\n")
        params = self.params
        params["baseDir"] = self.baseDir
        for k in sorted(self.params.keys()):
            f.write(k+"="+params[k]+"\n")
        f.write("\n")
            
        # ORIGINAL WRONG: for o in sorted(self.objectsByKey.values()):
        # variatn 1 (GOOD): for o in sorted(self.objectsByKey.values(),key=lambda x:x.name):
        for oName,o in sorted([(x.name,x) for x in self.objectsByKey.values()]):
            f.write("OBJECT\n")
            f.write("id="+o.name+"\n")
            f.write("type="+o.type+"\n")
            f.write("dir="+o.dir+"\n")
            f.write("NNN="+o.NNN+"\n")
            f.write("parents="  +  ','.join(o.parents) + "\n")
            f.write("deps="  +  ','.join(o.deps) + "\n")
            f.write("PARAMS\n")
            for p,v in sorted(o.pars.items()):
                f.write(p+"="+v+"\n")
            f.write("\n")
            
        f.write("END\n")
        f.close()
                            
    def loadFile(self,fname):
        hf = open(fname)

        done = 0
        if hf.readline().rstrip() != 'OBJECT_GRAPH':
            print "Not an OBJECT_GRAPH"
            raise
        for line in  hf:
            line = line.rstrip()
            if line == "":
                break
            self.fillHash(line, self.params);

        self.baseDir = self.params["baseDir"];
        
        for line in hf:
            line = line.rstrip()
            if line == "":
                done = 0;
                parents = []
                if req["parents"] != "":
                        parents = req["parents"].split(",")
                deps = []
                if req['deps'] != "":
                        deps = req["deps"].split(",")

                class OGO:
                        pass

                ob = OGO()
                ob.name = req['id']
                ob.type = req["type"]
                ob.dir = req["dir"]
                ob.NNN = req["NNN"]
                ob.parents = parents
                ob.deps = deps
                ob.pars = pars

                # ob = { "name":req["id"], "type":req["type"], "dir":req["dir"], \
                #        "parents":parents, "deps":deps, "pars":pars, "NNN":req["NNN"] }
        
                self.addObject(ob)
            elif line == "OBJECT":
                req = {}
                pars = {}
                ob = {}
                continue
            elif line == "PARAMS":
                done = 1
                continue
            elif line == "END":
                print "END\n"
            elif not done :
                self.fillHash(line, req);
            else:
                self.fillHash(line, pars);
                #self.printH(self.pars)
        hf.close()
        
if __name__ == "__main__":        
        a = objectgraph(sys.argv[1])
        a.writeObjectGraph(sys.argv[2])
