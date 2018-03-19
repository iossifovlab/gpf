
## Multi-allelic variants

| R A1 A2  |  R,R  |  R,A1  |  R,A2  | R,A1,A2 |  ?,?  |
|----------|-------|--------|--------|---------|-------|
|  now.A   |  none |   A1   |   A2   |  none   |  none |
|  now.B   |   A1  |   A1   |   A2   |   A1    |   A1  |
|----------|-------|--------|--------|---------|-------|
|> now.C   |   A1  |   A1   |   A2   |   A1    |   A1  |
|          |   A2  |        |        |   A2    |   A2  |
|----------|-------|--------|--------|---------|-------|
|  alt     | A1,A2 | A1,A2  | A1,A2  |  A1,A2  | A1,A2 |
|----------|-------|--------|--------|---------|-------|


## Discussion on roles filtering (2018-02-20)

```
    ##
    class AQN:
        def __init__(aqn,type,children==[],rVals==[]):
            aqn.type = type
            aqn.children = children
            aqn.type = rVals
        # type = 'in', '==', 'and', 'or', 'not'
        # children -- sub AQN 
        # rVals -- list of values
        def check(aqn,VALS):
            if aqn.type == 'all':
                assert not children and rVals
                return not rVals - VALS
            if aqn.type == 'any':
                assert not children and rVals
                return not rVals & VALS
            elif aqn.type == '==':
                assert not children and rVals
                return rVals == VALS
            elif aqn.type == 'not'
                assert len(aqn.children) == 1 and not rVals
                return not aqn.children[0].check(VALS)
            elif aqn.type == 'and'
                assert aqn.children and not rVals
                for chQN in aqn.children:
                    if not chQN.check(VALS):
                        return False
                return True
            elif aqn.type == 'or'
                assert aqn.children and not rVals
                for chQN in aqn.children:
                    if chQN.check(VALS):
                        return True
                return False
            else:
                assert False

    G = [o1.att, o2.att, ....]
    VALS = {o.att for o in G]
    if attQuery.check(VALS): ## attQuery is the top AQN
```

```
    "prb"              AQN('all', rVals=['prb'])
    "prb"              AQN('any', rVals=['prb'])


    "prb&sib"          AQN('all', rVals=['prb','sib']
    "prb and sib"      AQN('and',children=[
                                       AQN('in',rVals=['sib']),
                                       AQN('in',rVals=['prb'])
                                     ])
    "prb|sib"          AQN('any', rVals=['prb','sib']
    "prb or sib"       AQN('or', children=[
                                       AQN('in',rVals=['sib']),
                                       AQN('in',rVals=['prb'])
                                     ])
    "==(prb)"          AQN('==', rVals=['prb'])
    "==(prb,sib)"      AQN('==', rVals=['prb','sib'])
    "not sib"          AQN('not',children=[
                                       AQN('in',rVals=['sib'])
                                     ])
    "prb and not sib"  AQN('and', children=[
                                       AQN('all',rVals=['sib']),
                                       AQN('not',chidren=[
                                                           AQN('any',rVals=['prb'])
                                                         ]
                                     ])

    "prb and not mom|dad"  AQN('and', children=[
                                       AQN('all',rVals=['sib']),
                                       AQN('not',chidren=[
                                                           AQN('any',rVals=['prb'])
                                                         ]
                                     ])

    "prb and not mom&dad"  AQN('and', children=[
                                       AQN('all',rVals=['sib']),
                                       AQN('not',chidren=[
                                                           AQN('all',rVals=['prb'])
                                                         ]
                                     ])
    assert ATQ.parse("prb").check(VALS=set(['prb'])) == True
    assert ATQ.parse("prb").check(VALS=set([])) == False
    assert ATQ.parse("prb&sib").check(VALS=set(['prb'])) == False
    assert ATQ.parse("prb|sib").check(VALS=set(['prb'])) == True
    assert ATQ.parse("prb and not mom&dad").check(VALS=set(['prb','mom'])) == True
    assert ATQ.parse("prb and not mom&dad").check(VALS=set(['prb','mom','dad'])) == False
    assert ATQ.parse("prb and not mom|dad").check(VALS=set(['prb','mom'])) == False
    assert ATQ.parse("prb and not mom|dad").check(VALS=set(['prb','mom','dad'])) == False
    assert ATQ.parse("prb&sib").check(VALS=set(['prb','mom'])) == False
    assert ATQ.parse("prb|sib").check(VALS=set(['prb','mom'])) == True
    assert ATQ.parse("==(prb,sib)").check(VALS=set(['prb','sib'])) == True
    assert ATQ.parse("==(prb,sib)").check(VALS=set(['prb'])) == False
    assert ATQ.parse("==(prb,sib)").check(VALS=set(['prb','sib','mom'])) == False
```