Pedigree Generation Guide
=========================


Brief outline
#############

Starting off with a pedigree file that contains information about families and their individuals, we will run the file through two tools - the first one will add a column to the pedigree file - a layout column that contains the coordinates of each individual in the pedigree drawing that will be produced - and the second tool will generate a PDF file which contains the pedigree drawing, as well as some optional info.

This guide covers most cases; some specific notes regarding usage with studies containing multigenerational pedigrees are given at the end.


Prerequisites
#############

You will need a pedigree file (usually found with a .ped extension), which is a text file with delimiter-separated values (comma, tab, etc.), that contains the following columns:

Family ID:
  The values in this column must contain valid family IDs.
ID:
  IDs for separate individuals.
Father ID:
  A column that specifies the ID of the individual's father.
Mother ID:
  A column that specifies the ID of the individual's mother.
Sex:
  The sex of the individual.
Status:
  A column that specifies the status of the individual - whether he is affected or not.
Role:
  The role of the individual within his family.


Preparing the pedigree data
###########################

The pedigree data may require preparation beforehand. This section describes
 the requirements for pedigree data that must be met in order to use the tools.

In some cases, the initial pedigree file must be expanded with additional
individuals in order to correctly form some families. Following that,
individuals must be connected to their parents from the newly added
individuals.

Next, we need to replace the values in the sex, role and status columns
with those supported by the GPF system -
:ref:`sex <allowed_values_sex>`, :ref:`role <allowed_values_role>`,
:ref:`status <allowed_values_status>`. Each of these properties supports
synonyms, that are listed in the tables below.


Supported values for roles
++++++++++++++++++++++++++

====================================    ========================================================================================================
Role column canonical values            Synonyms (case insensitive)
====================================    ========================================================================================================
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
====================================    ========================================================================================================


Supported values for sex
++++++++++++++++++++++++

====================================    ========================================================================================================
Sex column canonical values             Synonyms (case insensitive)
====================================    ========================================================================================================
F                                       female, F, 2

M                                       male, M, 1

U                                       unspecified, U, 0
====================================    ========================================================================================================


Supported values for status
+++++++++++++++++++++++++++

====================================    ========================================================================================================
Sex column canonical values             Synonyms (case insensitive)
====================================    ========================================================================================================
affected                                affected, 2

unaffected                              unaffected, 1

unspecified                             unspecified, -, 0
====================================    ========================================================================================================


Common arguments for pedigree tools
###################################


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
        that specifies persons with role `proband`; this
        columns is used only when option `--ped-no-role` is
        specified. [default: None]

    --ped-no-header
        indicates that the provided pedigree file has no
        header. The pedigree column arguments will accept
        indices if this argument is given. [default: False]

    --ped-file-format PED_FILE_FORMAT
        Families file format. It should `pedigree` or
        `simple`for simple family format [default: pedigree]

    --ped-layout-mode PED_LAYOUT_MODE
        Layout mode specifies how pedigrees drawing of each
        family is handled. Available options are `generate`
        and `load`. When layout mode option is set to generate
        the loadertryes to generate a layout for the family
        pedigree. When `load` is specified, the loader tryes
        to load the layout from the layout column of the
        pedigree. [default: load]

    --ped-sep PED_SEP
        Families file field separator [default: `\t`]


Transform a pedigree file into default GPF form
###############################################

To transform a pedigree file into default GPF form one can use `ped2ped.py`
tool.

The tool has a '-h' or '--help' option, which brings out a list of possible
arguments and brief descriptions.


.. code-block:: bash

    ped2ped.py inital_pedigree_file.ped \
        ...<additional ped options>... \
        -o output_pedigree_file.ped


Visualize a pedigree file into PDF file
#######################################

To visualize a pedigree file into PDF file, that contains drawing of the
families pedigrees one can use `draw_pedigrees.py` tool:

.. code-block:: bash

    draw_pedigree.py pedigree_file_with_layout.ped \
        --mode report \
        ...<additional ped options>... \
        -o pedigree_drawing.pdf

The `--mode` option supports two values:

* `report`
    the tool will generate a family pedigree drawing for each **type**
    of family;

* `families`
    the tool will generate a family pedigree drawing for each  family.

