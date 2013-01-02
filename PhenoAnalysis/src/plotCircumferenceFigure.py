import phenoDB 
import matplotlib.pyplot as plt

rawDataFile = '/data/safe/leotta/sfari/v14/14_EVERYTHING.csv'

dt = phenoDB.loadFromRawTable(rawDataFile)

fields = [
    'hwhc.head_circumference',
    'hwhc.sibling1_head_circumference',
    'hwhc.sibling2_head_circumference',
    'hwhc.sibling3_head_circumference',
    'hwhc.sibling4_head_circumference',
    'hwhc.mother_head_circumference',
    'hwhc.father_head_circumference' ]


for f in fields:
    vls = [ float(dt[x]['variables'][f])  for x in dt.keys() if f in dt[x]['variables'] and dt[x]['member'] == "p1" ]
    print f, len(vls)
    if len(vls)>10:
        fig = plt.figure()   # <---
        figName="%s.png"%(f)
        plt.hist(vls,50)
        plt.title(f)   
        #plt.show()
        plt.savefig(figName, dpi=fig.dpi)
        plt.clf()

