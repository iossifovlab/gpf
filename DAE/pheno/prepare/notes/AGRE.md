## Problems with AGRE phenotype data

### Family `AU3472`

For individual `AU3472303` mother and father should be swapped

```
AssertionError: AU3472,AU3472201,Role.dad!=Role.step_mom
```

### Family `AU2232`

For individual `AU2232303` mom and dad should be swapped

```
AssertionError: AU2232,AU2232201,Role.dad!=Role.step_mom
```

### Family `AU1639`

For individual `AU1639305` mom and dad should be swapped

```
AssertionError: AU1639,AU1639201,Role.dad!=Role.step_mom
```


### Family `AU0567`


```
AU0567  Multiplex   AU056701    AU0567  1   0   0   Female      
AU0567  Multiplex   AU056702    AU0567  2   0   0   Male        
AU0567  Multiplex   AU056703    AU0567  3   2   1   Male        
AU0567  Multiplex   AU056704    AU0567  4   2   1   Female      
AU0567  Multiplex   AU056705    AU0567  5   2   1   Male        Autism  Autism
AU0567  Multiplex   AU056706    AU0567  6   2   1   Male        
AU0567  Multiplex   AU056707    AU0567  7   0   0   Male        
AU0567  Multiplex   AU056708    AU0567  8   7   4   Female      NQA Spectrum
```

Assigned roles are:

```
AU0567  AU056701    2   1   maternal_grandmother
AU0567  AU056702    1   1   maternal_grandfather
AU0567  AU056703    1   1   unknown
AU0567  AU056704    2   1   mom
AU0567  AU056705    1   2   unknown
AU0567  AU056706    1   1   unknown
AU0567  AU056707    1   1   dad
AU0567  AU056708    2   2   prb
```

### Family `AU1500`

```
AU1500  AU1500201       0               0               1       1       dad
AU1500  AU1500202       0               0               2       1       mom
AU1500  AU1500203       0               0               1       1       step_dad
AU1500  AU1500204       0               0               2       1       step_mom
AU1500  AU1500205       0               0               2       1       step_mom
AU1500  AU1500301       AU1500203       AU1500202       2       1       unknown
AU1500  AU1500302       AU1500203       AU1500202       1       1       unknown
AU1500  AU1500303       AU1500201       AU1500205       2       1       unknown
AU1500  AU1500304       AU1500201       AU1500204       2       1       unknown
AU1500  AU1500305       AU1500201       AU1500202       1       2       prb
AU1500  AU1500306       AU1500201       AU1500202       1       2       sib
```