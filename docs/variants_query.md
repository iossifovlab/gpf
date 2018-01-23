# Variants Query Interface

## De Novo and Transmitted Interfaces
```
    def get_denovo_variants(
        self, 
        inChild=None, 
        presentInChild=None,
        presentInParent=None, 

        gender=None,
        
        variantTypes=None, 
        effectTypes=None, 

        geneSyms=None,
        regionS=None, 
        genomicScores=[],

        familyIds=None, 

        limit=None

        callSet=None,
    ):
```

```
    def get_transmitted_variants(
        self, 
        inChild=None,
        presentInChild=None,
        presentInParent=None,

        gender=None,
        
        variantTypes=None,
        effectTypes=None,

        geneSyms=None,
        regionS=None,
        genomicScores=[]

        familyIds=None,

        limit=None,

        ultraRareOnly=False,
        minParentsCalled=0,
        maxAltFreqPrcnt=5.0,
        minAltFreqPrcnt=-1,

        TMM_ALL=False,
    ):
```


## Changes

### Filter by 'personIds'

```
    personIds=['11000.p1','11000.s1']
```

Should find only variants, that are present in any of individuals 
in `personIds` list.

### Filter by `role`

```
    role = ['mom', 'dad']
```

Should find only variants, that are present in individuals, whose role is one of
the roles in the list `role` and not found in individuals which 
role is not found in the list `role`.

Current list of roles:
```
    unknown
    mom
    dad
    step_mom
    step_dad
    prb
    sib
    child
    spouse
    maternal_cousin
    paternal_cousin
    maternal_uncle
    maternal_aunt
    paternal_uncle
    paternal_aunt
    maternal_half_sibling
    paternal_half_sibling
    maternal_grandmother
    maternal_grandfather
    paternal_grandmother
    paternal_grandfather
```

Configure group of roles, similar to `EffectTypes`.
* group `parent` should check roles `[mom, dad]`;
* group `cousin` should check roles `[maternal_cousin, paternal_cousin]`.


### Filter by `status`

```
    status = ['affected']
```

Should find only variants, that are present in individuals, whose status is one of
the statuses in the list `status` and not found in individuals which 
status is not found in the list `status`.

Supported statuses:
```
    affected
    unaffected
```



### Filter by inheritance

```
    inheritance = ['deNovo']
```

Available choices:
```
    De Novo
    Dominant
    Recessive
    Only in affected
    Only in unaffected
    Both
```

## Present in child filter and present in parent

## presentInChild

* proband only (affected only)   - `role = ['prb']; status=['affected']`
* sibling only (unaffected only) - `role = ['sib']; status=['unaffected']`
* proband and sibling            - `role = ['prb', 'sib'];

## presentInParent

* mother only - `role = ['mom']
* father only - `role = ['dad']
* mother and father - `role=['mom','dad']