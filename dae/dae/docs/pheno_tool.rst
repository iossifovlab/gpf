Phenotype tool
==============

Example usage of :class:`PhenoTool <dae.pheno_tool.tool.PhenoTool>` class
-------------------------------------------------------------------------
First some imports::

    from DAE import *
    from pheno_tool.tool import *



Then prepare studies to work with::

    studies = vDB.get_studies('ALL SSC')
    studies.append(vDB.get_study('w1202s766e611'))


Now we can create an instance of `PhenoTool` class to work with given set
of individuals::

    tool = PhenoTool(
             phdb, studies, roles=['prb', 'mom', 'dad'],
             measure_id='ssc_core_descriptive.ssc_diagnosis_nonverbal_iq',
    )

We can check the list of individuals that are subject to computation by this
particular instance of `PhenoTool` by using `list_of_subjects()` method::

    tool.list_of_subjects()

will output following dictionary::
 
    {
     u'14566.p1': Person(14566.p1; prb; M),
     u'14398.p1': Person(14398.p1; prb; M),
     u'14524.p1': Person(14524.p1; prb; M),
     u'12607.p1': Person(12607.p1; prb; M),
     ...
    }

We also have access to a `Pandas` data frame representing these subjects::

    persons = tool.list_of_subject_df()
    persons.head()


will output initial rows of the subjects dataframe::

       person_id family_id role gender  ssc_core_descriptive.ssc_diagnosis_nonverbal_iq  normalized
    2   11000.p1     11000  prb      M                                             78.0        78.0
    5   11001.p1     11001  prb      M                                            123.0       123.0
    8   11002.p1     11002  prb      F                                            111.0       111.0
    11  11003.p1     11003  prb      M                                            108.0       108.0
    14  11004.p1     11004  prb      M                                             74.0        74.0

Now we are ready for the actual computations. Let first get some set of gene
symbols::

    from DAE import get_gene_sets_symNS
    gt = get_gene_sets_symNS('main')
    gene_syms = gt.t2G['autism candidates from Iossifov PNAS 2015'].keys()

To perform the actual computation we use `calc` method of `PhenoTool`. We need
to pass to this method the specification of the variants::

    res = tool.calc(
        VT(
         effect_types=['LGDs'],
         gene_syms=gene_syms,
         present_in_child=['autism only', 'autism and unaffected'],
         present_in_parent=['neither'],
        ))


The returned object is of type
:class:`PhenoResult <dae.pheno_tool.pheno_common.PhenoResult>`. This class
could be queried about the results of the calculation::

    In [23]: res.positive_count
    Out[23]: 135

    In [24]: res.negative_count
    Out[24]: 2626

    In [25]: res.pvalue
    Out[25]: 1.5345885574583403e-07

We also have access to phenotypes and genotypes as dataframes::

    In [26]: res.genotypes_df.head()
    Out[26]:
       person_id gender role  variants
    2   11000.p1      M  prb         0
    5   11001.p1      M  prb         0
    8   11002.p1      F  prb         0
    11  11003.p1      M  prb         0
    14  11004.p1      M  prb         0

    In [27]: res.phenotypes_df.head()
    Out[27]:
       person_id role gender  ssc_core_descriptive.ssc_diagnosis_nonverbal_iq  normalized
    2   11000.p1  prb      M                                             78.0        78.0
    5   11001.p1  prb      M                                            123.0       123.0
    8   11002.p1  prb      F                                            111.0       111.0
    11  11003.p1  prb      M                                            108.0       108.0
    14  11004.p1  prb      M                                             74.0        74.0


and as dictionaries::


    In [28]: res.genotypes
    Out[28]:
    Counter({
             u'11046.p1': 0,
             u'14398.p1': 0,
             u'12547.p1': 1,
             u'14021.p1': 0,
             u'11264.p1': 0,
             u'11925.p1': 1,
             u'11249.p1': 0,
             ....
             })

    In [29]: res.phenotypes
    Out[29]:
    {u'14566.p1': {'gender': u'M',
      'normalized': 44.0,
      'person_id': u'14566.p1',
      'role': u'prb',
      'ssc_core_descriptive.ssc_diagnosis_nonverbal_iq': 44.0},
     u'14398.p1': {'gender': u'M',
      'normalized': 111.0,
      'person_id': u'14398.p1',
      'role': u'prb',
      'ssc_core_descriptive.ssc_diagnosis_nonverbal_iq': 111.0},
     u'14524.p1': {'gender': u'M',
      'normalized': 76.0,
      'person_id': u'14524.p1',
      'role': u'prb',
      'ssc_core_descriptive.ssc_diagnosis_nonverbal_iq': 76.0},
      ...
      }


Example usage of :class:`PhenoTool <dae.pheno_tool.tool.PhenoTool>` class with pheno filters
--------------------------------------------------------------------------------------------

The `PhenoTool` class supports different ways to specify which individuals are
subject to the calculations. We can use `roles`, `measure_id`, `normalize_by`
and `pheno_filters` arguments in the `PhenoTool` constructor. For example if we
specify `roles` and `measure_id` the tool will use individuals of the specified
roles and has the specified measurement::

    tool = PhenoTool(phdb, studies, roles=['prb', 'sib'],
                measure_id="ssc_commonly_used.head_circumference")

and if whe check list of subjects::

    In [41]: len(tool.list_of_subjects())
    Out[41]: 5166

If we specify a normalization, then the list of individuals should have
measurements for normalization too::

    tool = PhenoTool(phdb, studies, roles=['prb', 'sib'],
                measure_id="ssc_commonly_used.head_circumference",
                normalize_by=['pheno_common.age'])

    In [45]: len(tool.list_of_subjects())
    Out[45]: 4869

Additionally we can use `pheno_filters` argument. Let us specify only
individuals that are of `white` race::

    tool = PhenoTool(phdb, studies, roles=['prb', 'sib'],
                measure_id="ssc_commonly_used.head_circumference",
                pheno_filters={
                    'pheno_common.race': set(['white'])
                })

    In [47]: len(tool.list_of_subjects())
    Out[47]: 3983

or::

    tool = PhenoTool(phdb, studies, roles=['prb', 'sib'],
         measure_id="ssc_commonly_used.head_circumference",
         pheno_filters={
            'pheno_common.race': set(['white', 'asian']),
         })

    In [51]: len(tool.list_of_subjects())
    Out[51]: 4174


Using `pheno_filters` we can also specify ranges of values for given
measurement::

    tool = PhenoTool(phdb, studies, roles=['prb', 'sib'],
          measure_id="ssc_commonly_used.head_circumference",
          pheno_filters={
             'pheno_common.race': set(['white', 'asian']),
             'pheno_common.age': (200, 220),
          })

    In [53]: len(tool.list_of_subjects())
    Out[53]: 145

Example with `vineland_ii`
--------------------------

Example for iterating on many measures::

    from DAE import *
    from pheno_tool.tool import *
    from pheno_tool.genotype_helper import GenotypeHelper


    studies = vDB.get_studies('IossifovWE2014')
    genotype_helper = GenotypeHelper(studies)

    effect_types = ['LGDs', 'missense', 'nonsynonymous']

    genotypes = {}
    for et in effect_types:
        variants_type = VT(
            effect_types=[et],
            present_in_parent=['neither'],
            present_in_child=['autism only',
                              'autism and unaffected',
                              'unaffected only']
        )
        persons_variants = genotype_helper.get_persons_variants_df(variants_type)
        genotypes[et] = persons_variants

    result = {}

    for measure_id in phdb.get_instrument_measures('vineland_ii'):
        measure = phdb.get_measure(measure_id)
        if measure.measure_type != "continuous":
            continue

        cols = [measure_id]
        for role in ['prb', 'sib']:
            tool = PhenoTool(phdb, studies, roles=[role], measure_id=measure_id)
            for et in effect_types:
                print("working on: {}, {}, {}".format(measure_id, role, et))
                res = tool.calc(genotypes[et])
                cols.append("%.3f" % res.pvalue)
        result[measure_id] = cols


Classes and Functions
---------------------
.. toctree::
   :maxdepth: 3

   modules/dae.pheno_tool

