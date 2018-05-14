'''
Created on Jan 31, 2013

@author: Tony
'''

from builtins import object
import SfariVariable
import csv

# a keeper for variables
class SfariVariableTracker(object):   
    
    def __init__(self):
        self.variables = {}
    
    def count(self):
        return len(self.variables)
        
    def variableNames(self):
        return list(self.variables.keys())
    
    def getVariable(self, name):
        if name in self.variables:            
            return self.variables[name]
        else:
            return None 
            
    def add(self, name, member, source):
        
        if name not in self.variables:
            var = SfariVariable.SfariVariable(name)
            var.source = source
            self.variables[name] = var
        else:
            var = self.variables[name]
            
        var.addMemberReference(member)
                        
    def translate(self, input):
                       
        if (input == 'p'):                                         
            code = 'p1'                                                                
        elif (input == 's'):
            code = 's1'
        elif (input == 'm'):
            code = 'mo'
        elif (input == 'f'):
            code = 'fa'
        elif (input == 't'):
            code = 't1'
        else:
            code = "e1"  #error                
        return code    
        
    def save(self, filename):
        f = open(filename, "wb")                       
        i = 1                
        writer = csv.writer(f)
        
        row = []    
        row.append("Variable")
        row.append("p1")        
        row.append("s1")
        row.append("t1")
        row.append("mo")
        row.append("fa")
        row.append("total")        
        writer.writerow(row)
            
        keys = sorted(self.variables.keys())
                
        grandTotal=0          
        for key in keys:
            variable = self.variables[key]         
            row = []    
            row.append(variable.name)
            row.append(variable.checkReference("p1"))        
            row.append(variable.checkReference("s1"))
            row.append(variable.checkReference("t1"))
            row.append(variable.checkReference("mo"))
            row.append(variable.checkReference("fa"))
            
            total = variable.checkReference("p1")+variable.checkReference("s1")+variable.checkReference("t1")+variable.checkReference("mo")+variable.checkReference("fa")
            grandTotal+=total
            row.append(total)
            
            writer.writerow(row)            
                                
        row = []    
        row.append('')
        row.append('')
        row.append('')
        row.append('')
        row.append('')
        row.append('')        
        row.append(grandTotal)        
        writer.writerow(row)            
                                        
        f.close()          
        
        
        
        