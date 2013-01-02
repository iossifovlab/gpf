import phenoDB 

rawDataFile = '/data/safe/leotta/sfari/v14/14_EVERYTHING.csv'

dt = phenoDB.loadFromRawTable(rawDataFile)

print dt['12449.p1']['variables']['hwhc.head_circumference']

mt,members = phenoDB.imputeMetaData(dt)

phenoDB.createMetaDataReport(mt, members, "demoReport.csv")



