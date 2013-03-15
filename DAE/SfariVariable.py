'''
Created on Jan 31, 2013

@author: Tony
'''
# Tracks the family references of a variable
class SfariVariable:
    
    def __init__(self, name):
        self.name = name
        self.dataType = 'unknown'
        self.uniqueValues = 0
        self.members = []
        self.values = {}
        self.source = '' # which CSV file did this variable come from EVERYTHING or COMON_CORE?
    
    # increment a family member count
    def addMemberReference(self, member):
        if member not in self.members:
            self.members.append(member)
    
    def checkReference(self, member):
        if member in self.members:
            return 1
        else:
            return 0