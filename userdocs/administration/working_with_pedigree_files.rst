.. _working_with_pedigrees:


Working With Pedigree Files Guide
=================================

Brief outline
#############

The GPF system has a flexible support for various input format of pedigree file.
When loaded the pedigree is kept in an internal representation. The `ped2ped.py`
tool allows loading the input pedigree file and storing it into the
canonical GPF pedigree representation.

Additionally GPF has a tool `draw_pedigree.py`
that could generate a PDF file with drawings of all pedigrees loaded from
the input.

Input pedigree file
###################

A pedigree file (usually found with a .ped extension) is a text file with
delimiter-separated values (comma, tab, etc.). Each row in this file
describes an individual. 

The file should contain the following columns:

Family ID:
  Contains family ID for the individual.
Person ID:
  Contains person ID for the individual.
Father ID:
  Contains the person ID of the individual's father. If the individual
  is without a specified father this column contains `0` or is left empty.
Mother ID:
  Contains the person ID of the individual's mother. If the individual
  is without a specified mother this column contains `0` or is left empty.
Sex:
  The sex of the individual.
Status:
  The affected status of the individual - whether they are affected or not.

The pedigree file can contain more columns, that specify different attributes
for individuals.

Canonical pedigree file
#######################

The canonical pedigree file matches closely the internal representation of
the pedigree data. Each line in the pedigree file specifies the attributes
of an individual. 

The columns in a canonical pedigree file are:

familyId:
    Contains IDs for families included in the pedigree file.

personId:
    Contains IDs for individuals included in the pedigree file. The assumption is that
    person IDs are unique across the whole pedigree file.

momId:
    Contains the ID of the individual's mother. If a mother is not specified this column
    should contain `0` or should left be empty.

dadId:
    Contains the ID of the individual's father. If a father is not specified this column
    should contain `0` or should be left empty.

sex:
    The sex of the individual. Supported values for the `sex` column are described in
    :ref:`Supported values for sex`

status:
    The affected status of the individual. Supported values for the `status` column
    are described in
    :ref:`supported values for status`

role:
    The role of the individual. Supported values for the `role` column are described in
    :ref:`supported values for role`

sampleId:
    This column is used to map an individual to the sample ID used in the genotypes
    file(s) (e.g a VCF file(s)). If this column is not specified in the input pedigree,
    it will be created and values will coincide with the `personId` column.

layout:
    This column is optional. The suported format is following: `<rank>:<x>,<y>`, where

    * `<rank>` is the rank of the individual in the family, where the individuals from 
      the earliest generation in the family have a rank of 1, the individuals from the next
      generation have a rank of 2, et. For example in a nuclear family, the mother and father have
      a rank of 1 and the children have a rank of 2.
    * `<x>` is the `x`-coordinate of the individual icon.
    * `<y>` is the `y`-coordinate of the individual icon.

generated:
    This column specifies if a given individual is `generated`. The supported values in this
    column are `True` and `False`.

    When the pedigree file contains not full families, the GPF tools
    add individuals to the family to make the family full. 
    
    For example, if a family
    contains two individuals - mother and proband, - the GPF adds father to this family
    to make proper visualization of the family.

    These additional individuals are marked as `generated` and are not used in any downstream
    analysis. Their use is purely for visualization purposes.

When the input pedigree contains any additional columns the GPF tools keep these columns in the
canonical representation.


Possible input pedigree file structures
#######################################

When the input pedigree file is given to the GPF system it tries to transform it into
the canonical representation described in
:ref:`canonical pedigree file`.

GPF system uses individuals' roles for various queries. 
When the `role` column is not present in the
input pedigree file, the GPF system tries to deduce the role of each individual
in respect to the family's proband.

The GPF system has different strategies to infer the `role` of each individual.
Which strategy to use depends on the input data.


Plain pedigree (familyId, personId, momId, dadId, sex, status) 
--------------------------------------------------------------

Often, the pedigree does not contain a role column. In this case the 
GPF system uses the following approach:

* Assign a role proband to the first affected child in each family.
* The roles of all other members in the family are inferred with
  respect to the proband.

.. note::

    If no proband is found, all the roles will be set to `unknown`. 

Example: simple pedigree file
"""""""""""""""""""""""""""""

Let's say we have the following input pedigree file:

========  ========  =====  =====  ===  ==========
familyId  personId  momId  dadId  sex  status    
========  ========  =====  =====  ===  ==========
f1        f1.01     0      0      F    unaffected
f1        f1.02     0      0      M    unaffected
f1        f1.03     f1.01  f1.02  F    affected  
f1        f1.04     f1.01  f1.02  M    affected  
f1        f1.05     0      0      M    unaffected
f1        f1.06     f1.01  f1.05  F    unaffected
========  ========  =====  =====  ===  ==========

To assign roles to the members of family `f1` the GPF system will look
for the first affected child in the `f1` family - this will be `f1.03` and this
individual will get a role `proband`. The mother and father of `f1.03`
will become with roles `mom` and `dad` and hence `f1.01` is going to have
the role `mom` and `f1.02` - role `dad`. The sibling of `f1.03` will have the role
`sib` and hence `f1.04` is going to have the role `sib`. 

This process
continues until all individuals in the family have their roles set.

========  ========  =====  =====  ===  ==========  =======================
familyId  personId  momId  dadId  sex  status      role
========  ========  =====  =====  ===  ==========  =======================
f1        f1.01     0      0      F    unaffected  mom
f1        f1.02     0      0      M    unaffected  dad
f1        f1.03     f1.01  f1.02  F    affected    prb
f1        f1.04     f1.01  f1.02  M    affected    sib
f1        f1.05     0      0      M    unaffected  step_dad
f1        f1.06     f1.01  f1.05  F    unaffected  maternal_half_sibling
========  ========  =====  =====  ===  ==========  =======================




Pedigree with proband column (familyId, personId, momId, dadId, sex, status, prb) 
---------------------------------------------------------------------------------

When the strategy described in
:ref:`plain pedigree (familyid, personid, momid, dadid, sex, status)`
is not appropriate the GPF can use a pedigree file with a proband column, that
specifies which individual in the family has the role proband.

* The first individual in the family for whom the `proband` column has value
  `True` recivies the role `proband`.
* The roles of all other individuals are inferred with respect to the proband.

.. note::

    If no proband is indicated, the tools fallback into the strategy described in
    :ref:`plain pedigree (familyid, personid, momid, dadid, sex, status)`

.. note::

    If more than one proband is selected, the role `prb` is assigned to the first of them
    and the rest of the roles are inferred with respect to the first (in the pedigree file)
    proband. 


Example: pedigree file with *prb* column
""""""""""""""""""""""""""""""""""""""""

Let's say we have the following input pedigree file:

========  ========  =====  =====  ===  ==========  =====
familyId  personId  momId  dadId  sex  status      prb
========  ========  =====  =====  ===  ==========  =====
f1        f1.01     0      0      F    unaffected  0
f1        f1.02     0      0      M    unaffected  0
f1        f1.03     f1.01  f1.02  F    affected    0
f1        f1.04     f1.01  f1.02  M    affected    1
f1        f1.05     0      0      M    unaffected  0
f1        f1.06     f1.01  f1.05  F    unaffected  0
========  ========  =====  =====  ===  ==========  =====

Note the `prb` column that specifies which individual has the role proband.
So the `f1.04` recivies role `prb`. The mother and father of `f1.04`
will have roles `mom` and `dad` and hence `f1.01` is going to have
the role `mom` and `f1.02` - role `dad`. The sibling of `f1.04` will have the role
`sib` and hence `f1.03` is going to have the role `sib`. 

This process
continues until all individuals in the family have their roles set.

========  ========  =====  =====  ===  ==========  =======================
familyId  personId  momId  dadId  sex  status      role
========  ========  =====  =====  ===  ==========  =======================
f1        f1.01     0      0      F    unaffected  mom
f1        f1.02     0      0      M    unaffected  dad
f1        f1.03     f1.01  f1.02  F    affected    sib
f1        f1.04     f1.01  f1.02  M    affected    prb
f1        f1.05     0      0      M    unaffected  step_dad
f1        f1.06     f1.01  f1.05  F    unaffected  maternal_half_sibling
========  ========  =====  =====  ===  ==========  =======================


Pedigree with role column (familyId, personId, momId, dadId, sex, status, role) 
-------------------------------------------------------------------------------

When a `role` column is defined in the input pedigree it becomes the source of truth
about individuals' roles. Whatever is saved in this column is interpreted as the role
of the individual.

Example: pedigree with role column
""""""""""""""""""""""""""""""""""

========  ========  =====  =====  ===  ==========  =======================
familyId  personId  momId  dadId  sex  status      role
========  ========  =====  =====  ===  ==========  =======================
f1        f1.01     0      0      F    unaffected  mom
f1        f1.02     0      0      M    unaffected  dad
f1        f1.03     f1.01  f1.02  F    affected    prb
f1        f1.04     f1.01  f1.02  M    affected    sib
f1        f1.05     0      0      M    unaffected  step_dad
f1        f1.06     f1.01  f1.05  F    unaffected  maternal_half_sibling
========  ========  =====  =====  ===  ==========  =======================


Full canonical pedigree
-----------------------

The canonical pedigree file contains the `role` column and so, the GPF system uses this
column to assign the role of each individual.


.. todo:: 
    The loader will be upset (ERROR) if the role is not one of the recognized, names
    or synonyms. 

    The loader will output a WARNING if no proband is assigned for a family
    (can be suppressed with an argument???) OR consider it an ERROR condition that
    can be suppressed with an argument. 

    The loader will output a WARNING if more than one proband is assigned for a
    family??
    (can be suppressed with an argument???) 


Preparing the pedigree data
###########################

The pedigree data may require preparation beforehand. This section describes
the requirements for pedigree data that must be met to use the tools.

In some cases, the initial pedigree file must be expanded with additional
individuals to correctly form some families. Following that,
individuals must be connected to their parents from the newly added
individuals.

We must ensure the values in the sex, status and role columns in the file
are supported by the GPF system. You can see a list of the supported
values here - :ref:`supported values for sex`,
:ref:`supported values for status`,
:ref:`supported values for role`.

Also, these properties support synonyms, which are listed in the tables below:


Supported values for sex
########################

====================================    ================================================
Sex column canonical values             Synonyms (case insensitive)
====================================    ================================================
F                                       female, F, 2

M                                       male, M, 1

U                                       unspecified, U, 0
====================================    ================================================


Supported values for status
###########################

====================================    ================================================
Sex column canonical values             Synonyms (case insensitive)
====================================    ================================================
affected                                affected, 2

unaffected                              unaffected, 1

unspecified                             unspecified, -, 0
====================================    ================================================



Supported values for role
#########################

====================================    ================================================
Role column canonical values            Synonyms (case insensitive)
====================================    ================================================
prb                                     proband, prb

sib                                     sibling, younger sibling, older sibling, sib

maternal_grandmother                    maternal grandmother, maternal_grandmother

maternal_grandfather                    maternal grandfather, maternal_grandfather

paternal_grandmother                    paternal grandmother, paternal_grandmother

paternal_grandfather                    paternal grandfather, paternal_grandfather

mom                                     mom, mother

dad                                     dad, father

child                                   child

maternal_half_sibling                   maternal half sibling, maternal_half_sibling

paternal_half_sibling                   paternal half sibling, paternal_half_sibling

half_sibling                            half sibling, half_sibling

maternal_aunt                           maternal aunt, maternal_aunt

maternal_uncle                          maternal uncle, maternal_uncle

paternal_aunt                           paternal aunt, paternal_aunt

paternal_uncle                          paternal uncle, paternal_uncle

maternal_cousin                         maternal cousin, maternal_cousin

paternal_cousin                         paternal cousin, paternal_cousin

step_mom                                step mom, step_mom, step mother

step_dad                                step dad, step_dad, step father

spouse                                  spouse

unknown                                 unknown
====================================    ================================================


Common arguments for the pedigree tools
#######################################


positional arguments:                                                                                                                                                                                                                                                                                                                                                                     
  <families filename>   families filename in pedigree or simple family format                                                                                                                                                                                                                                                                                                             
                                                                                                                                                                                                                                                                                                                                                                                          
optional arguments:
    --ped-family PED_FAMILY                                                                                                                                                                                                                                                                                                                                                                 
        specify the name of the column in the pedigree file                                                                                                                                                                                                                                                                                                               
        that holds the ID of the family the person belongs to                                                                                                                                                                                                                                                                                                             
        [default: familyId]                                                                                                                                                                                                                                                                                                                                               

    --ped-person PED_PERSON                                                                                                                                                                                                                                                                                                                                                                 
        specify the name of the column in the pedigree file                                                                                                                                                                                                                                                                                                               
        that holds the person's ID [default: personId]

    --ped-mom PED_MOM   
        specify the name of the column in the pedigree file                                                                                                                                                                                                                                                                                                               
        that holds the ID of the person's mother [default:                                                                                                                                                                                                                                                                                                                
        momId]

    --ped-dad PED_DAD
        specify the name of the column in the pedigree file                                                                                                                                                                                                                                                                                                               
        that holds the ID of the person's father [default:                                                                                                                                                                                                                                                                                                                
        dadId]                                                                                                                                                                                                                                                                                                                                                            

    --ped-sex PED_SEX
        specify the name of the column in the pedigree file                                                                                                                                                                                                                                                                                                               
        that holds the sex of the person [default: sex]                                                                                                                                                                                                                                                                                                                   

    --ped-status PED_STATUS                                                                                                                                                                                                                                                                                                                                                                 
        specify the name of the column in the pedigree file                                                                                                                                                                                                                                                                                                               
        that holds the status of the person [default: status]                                                                                                                                                                                                                                                                                                             

    --ped-role PED_ROLE
        specify the name of the column in the pedigree file
        that holds the role of the person [default: role]

    --ped-no-role
        indicates that the provided pedigree file has no role
        column. If this argument is provided, the import tool
        will guess the roles of individuals and write them in
        a "role" column.

    --ped-proband PED_PROBAND
        specify the name of the column in the pedigree file
        that specifies persons with role `proband`;
        this column is used only when option `--ped-no-role` is
        specified. [default: None]

    --ped-no-header
        indicates that the provided pedigree file has no
        header. The pedigree column arguments will accept
        indices if this argument is given. [default: False]

    --ped-file-format PED_FILE_FORMAT
        Families file format. It should `pedigree` or
        `simple` for simple family format [default: pedigree]

    --ped-layout-mode PED_LAYOUT_MODE
        Layout mode specifies how pedigrees drawing of each
        family is handled. Available options are `generate`
        and `load`. When the layout mode option is set to
        `generate``
        the loader tries to generate a layout for each family
        pedigree. When `load` is specified, the loader tries
        to load the layout from the layout column of the
        pedigree. [default: load]

    --ped-sep PED_SEP
        Families file field separator [default: `\t`]

    -o OUTPUT_FILENAME
        specify the name of the output file


Transform a pedigree file into canonical GPF form
#################################################

To transform a pedigree file into canonical GPF form you can use the `ped2ped.py`
tool.
To see the tool's full functionality use::

    ped2ped.py --help

To demonstrate how it works, we will use the sample data.
To standardize the ``example_families.ped`` file use:

.. code-block:: bash

    ped2ped.py example_families.ped \
    --ped-layout-mode generate -o example_family_standardized.ped

The output ``example_family_standardized.ped`` file has two newly generated
columns - `sampleId` and `layout`, which are used by the GPF system.

The `ped2ped.py` tool can also process pedigree files with noncanonical column names.
For such cases, it has arguments that can be used to specify which column contains the
family id, role, status, sex, etc. For example, see the case of the
``example_families_with_noncanonical_column_names.ped`` file:

.. code-block:: bash

    ped2ped.py example_families_with_noncanonical_column_names.ped \
    --ped-family Family_id --ped-person Person_id --ped-dad Dad_id --ped-mom Mom_id \
    --ped-sex Sex --ped-status Status --ped-role Role \
    --ped-layout-mode generate -o example_families_from_noncanonical_column_names.ped

The `ped2ped.py` tool can also process pedigree files without headers.
One such file is ``example_families_without_header.ped``.
In this case, we have to map the column's index to a specific column name. The same way we mapped
'Family_id' to the family id column in the upper example, here we map the first column to family id
(Keep in mind the column indices begin from 0). See the example below:

.. code-block::

    ped2ped.py example_families_without_header.ped \
    --ped-no-header --ped-family 0 --ped-person 1 --ped-dad 2 --ped-mom 3 \
    --ped-sex 4 --ped-status 5 --ped-role 6 \
    --ped-layout-mode generate -o example_families_from_no_header.ped

Visualize a pedigree file into a PDF file
#########################################

To visualize a pedigree file into a PDF file, containing drawings of the
family pedigrees you can use the `draw_pedigrees.py` tool.
To see its full functionality use::

    draw_pedigree.py --help

Notice that it shares a lot of common flags with the `ped2ped.py` tool.
Similar to the `ped2ped.py` tool,
it can also process pedigree files with noncanonically named columns or without a header.

In addition to that, it has a ``--mode`` flag, which supports two values:

* `report`
    the tool will generate a family pedigree drawing for **each unique family structure** family

* `families`
    the tool will generate a family pedigree drawing for **every individual** family

To demonstrate how to use the `draw_pedigree.py` tool we will visualize the ``example_families.ped`` file:

.. code-block:: bash

    draw_pedigree.py example_families.ped -o example_families_visualization.pdf

This command outputs the ``example_families_visualization.pdf`` file with the pedigree
drawings.
