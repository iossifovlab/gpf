# Variants Query Interface

## Summary Variants
    
Summary variants are described by following attributes:

* study
* location
    * begin
    * end
* variant_type
* variant
    * ref
    * alt
* gene_effects
* effect_details
* frequencies??
* genomic_scores

**Note:** should we support multiple variant_types/variants in each variant? 
Or we could create several variants, each one of them with different 
variant_types/variants? E.g.:
```text
variant:
    study: IossifovWE2017
    location:
        begin: 1:16255763
        end: 1:16255763
    variants:
        ins(A)
        sub(G->A)
    ...
```
vs
```text
variant: 
    study: IossifovWE2017
    location:
        begin: 1:16255763
        end: 1:16255763
    variants:
        ins(A)
        ...
variant:
    study: IossifovWE2017
    location:
        begin: 1:16255763
        end: 1:16255763
    variants:
        sub(G->A)
    ...
```


## Family Variants

Family variants have all the attributes of summary variants and also have following
additional attributes:

* family_id
* members_in_order
* best_state
* counts



## Genotype in Families Interface

We need to have an object, that implements following methods:

* most commonly used method 

    ```text
    query_variant(**kwargs)
    ```
    This method returns iterator to variants in families that match to specified
    query parameters.
    
* helper method for finding summary variants - variants without family info:

    ```text
    query_summary_variants(**kwargs)
    ```

## Query variants filters:

* `regions` (`positions`)
    should accept list of regions or positions, e.g.:
    ```text
    ['chr1':100000000-110000000, 'chr2':500000-600000, chr3:500000]
    ```
    The query interface should return variants, which have location inside
    one of the passed regions.

* `variant_types`
    supported variant types are:
    ```text
    sub, ins, del, cnv, vcf
    ```
    `vcf` is used to represent complex variants, that could not be described
    by one of the other variant types. 
    
    The interface should accept list of variant types. Returned variants should
    match one of the requested variant types.


* `effect_types` - the list of supported `effect_types` is:
    ```text
    3'UTR,
    3'UTR-intron,
    5'UTR,
    5'UTR-intron,
    frame-shift,
    intergenic,
    intron,
    missense,
    no-frame-shift,
    no-frame-shift-newStop,
    noEnd,
    noStart,
    non-coding,
    non-coding-intron,
    nonsense,
    splice-site,
    synonymous,
    CDS,
    CNV+,
    CNV-,
    ```
    The interface should accept list of effect types and return variants, which 
    types match at least one of request effect types.

* `genes` (`gene_symbols`)
    The interace should accept list of gene symbos and should return variants, that
    have effect at least in one of the requested symbols.

* `genomic_scores`
    - genomic scores query should accept list of genomic scores range specifiers. Each
    genomic score range specifier should contain following params:
    * `score` - score name (score id)
    * `min` - score minimal value
    * `max` - score maximal value
    Returned variants should have the specified genomic score `score` and the value
    of the genomic score should be inside the interval `[min, max]`. 
    
    When multiple
    genomic scores are specified, then the variant should match all of the specified
    genomic score ranges.

* `sexes`
    - accepts list of sexes. Supported sexes are `female`, `male` and `unspecified`.
    When passed the method should return variants that are found in individuals with
    specified sex.

* `roles` - accepts list of roles. Supprted roles are:
    ```text
    unknown 
    mom 
    dad 
    step_mom 
    step_dad 
    prb 
    sib 
    child 
    spouse 
    ...
    ```
    Grouping of roles should be supported in the interface.
    
    When list of roles is passed, the variants
    that are returned should be found in individuals, that have at least one of 
    the specified roles.
    
    **Alternatively**, the returned family variants should be found in individuals with
    all specified roles in the family. E.g.:
    * `roles=[prb,sib]`
    should return variants that are found in both `prb` and `sib` in 
    each family;
    * `roles=[prb,dad]` should return variants that are found in both `prb` and
    `dad` in each family returned;

* `inheritance_types` specified type of inheritance of variants inside families.
    Supported `inhteritance_types` are:
    * `de Novo` - selects de Novo variants;
    * `medelian` - alleles are transferred from parents to childrens according
        Mendel's laws of inheritance
    * `ommission`
    * `reference`
    * `other`
    * `unknown`


* `frequency`
    ???


* `family_ids` - accepts list of family IDs. When passed, the query method
    should return variants that occur at least in one of specified families

* `person_ids` - accepts list of person IDs (individual IDs). When pass the query
    method should return variants that occur in at least one of the specified
    individuals.



# Previous iteration
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

### Present in child filter and present in parent

#### presentInChild

* proband only (affected only)   - `role = ['prb']; status=['affected']`
* sibling only (unaffected only) - `role = ['sib']; status=['unaffected']`
* proband and sibling            - `role = ['prb', 'sib'];

#### presentInParent

* mother only - `role = ['mom']
* father only - `role = ['dad']
* mother and father - `role=['mom','dad']