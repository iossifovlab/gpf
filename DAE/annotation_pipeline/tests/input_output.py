BASE_INPUT = [
    '1\t4:4372372973\tsub(A->C)\n',
    '5\t10:4372372973\tsub(G->A)\n',
    '3\tX:4372\tins(AAA)\n',
    '6\tY:4372372973\tdel(2)\n'
]

SPLIT_COLUMN_INPUT = [
    '1\t4:4372372973\tsub(A->C)\n',
    '5\t10:4372372973|1:8493943843\tsub(G->A)\n',
    '3\tX:4372\tins(AAA)\n',
    '6\tY:4372372973\tdel(2)\n'
]

MULTIPLE_HEADERS_INPUT = [
    '#Second header\n',
    '1\t4:4372372973\tsub(A->C)\n',
    '5\t10:4372372973\tsub(G->A)\n',
    '#Last header\n',
    '3\tX:4372\tins(AAA)\n',
    '6\tY:4372372973\tdel(2)\n'
]

BASE_OUTPUT = """#id\tlocation\tvariant\tloc
1\t4:4372372973\tsub(A->C)\t4:437237297
5\t10:4372372973\tsub(G->A)\t10:437237297
3\tX:4372\tins(AAA)\tX:437
6\tY:4372372973\tdel(2)\tY:437237297
"""

REANNOTATE_OUTPUT = """#id\tlocation\tvariant
1\t4:437237297\tsub(A->C)
5\t10:437237297\tsub(G->A)
3\tX:437\tins(AAA)
6\tY:437237297\tdel(2)
"""

DEFAULT_ARGUMENTS_OUTPUT = """#id\tlocation\tvariant\tlocation
1\t4:4372372973\tsub(A->C)\t4:4372372
5\t10:4372372973\tsub(G->A)\t10:4372372
3\tX:4372\tins(AAA)\tX:4
6\tY:4372372973\tdel(2)\tY:4372372
"""

SPLIT_COLUMN_OUTPUT = """#id\tlocation\tvariant\tloc
1\t4:4372372973\tsub(A->C)\t4:437237297
5\t10:4372372973|1:8493943843\tsub(G->A)\t10:437237297|1:849394384
3\tX:4372\tins(AAA)\tX:437
6\tY:4372372973\tdel(2)\tY:437237297
"""

MULTIPLE_HEADERS_OUTPUT = """#id\tlocation\tvariant\tloc
#Second header
1\t4:4372372973\tsub(A->C)\t4:437237297
5\t10:4372372973\tsub(G->A)\t10:437237297
#Last header
3\tX:4372\tins(AAA)\tX:437
6\tY:4372372973\tdel(2)\tY:437237297
"""
