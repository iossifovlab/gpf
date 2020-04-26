.. _working_with_pedigrees:


Working With Pedigree Files Guide
=================================

Brief outline
#############
Starting off with a pedigree file that contains information about families and their individuals, we will run the file through two tools.
The first one is `ped2ped.py` whose task is to standardize the pedigree file to suit the GPF system. It can add a layout column that
contains the coordinates of each individual in the pedigree drawing. It can also add headers to files that don't have them.
The second tool is `draw_pedigree.py` which will generate a PDF file with the pedigree drawings.
There are provided examples in the end of this guide demonstrating how to use these tools.


Prerequisites
#############
The sample data used in the examples of this guide can be found `here <https://iossifovlab.com/distribution/public/tutorial_examples/>`_.

A pedigree file (usually found with a .ped extension) is a text file with delimiter-separated values (comma, tab, etc.),
that contains the following columns:

Family ID:
  IDs for families.
Person ID:
  IDs for separate individuals.
Father ID:
  IDs of the individual's father.
Mother ID:
  IDs of the individual's mother.
Sex:
  The sex of the individual.
Status:
  The status of the individual - whether they are affected or not.
Role:
  The role of the individual within their family.


Preparing the pedigree data
###########################

The pedigree data may require preparation beforehand. This section describes
the requirements for pedigree data that must be met in order to use the tools.

In some cases, the initial pedigree file must be expanded with additional
individuals in order to correctly form some families. Following that,
individuals must be connected to their parents from the newly added
individuals.

We must ensure the values in the sex, status and role columns in the file are supported by
the GPF system. You can see a list of the supported values here - :ref:`sex <allowed_values_sex>`, :ref:`status <allowed_values_status>`,
:ref:`role <allowed_values_role>`. Also these properties support synonyms, which are listed on the tables below:


Supported values for `sex`
++++++++++++++++++++++++++

====================================    ========================================================================================================
Sex column canonical values             Synonyms (case insensitive)
====================================    ========================================================================================================
F                                       female, F, 2

M                                       male, M, 1

U                                       unspecified, U, 0
====================================    ========================================================================================================


Supported values for `status`
+++++++++++++++++++++++++++++

====================================    ========================================================================================================
Sex column canonical values             Synonyms (case insensitive)
====================================    ========================================================================================================
affected                                affected, 2

unaffected                              unaffected, 1

unspecified                             unspecified, -, 0
====================================    ========================================================================================================



Supported values for `role`
++++++++++++++++++++++++++++

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
        that specifies persons with role `proband`; this
        columns is used only when option `--ped-no-role` is
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
        and `load`. When layout mode option is set to generate
        the loadertryes to generate a layout for the family
        pedigree. When `load` is specified, the loader tryes
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

The output ``example_family_standardized.ped`` file has two newly generated columns - `sampleId` and `layout`, which
are used by the GPF system.

The `ped2ped.py` tool can also process pedigree files with noncanonical column names.
For such cases it has arguments that can be used to specify which column contains the
family id / role / sex / etc. For example, see the case of the ``example_families_with_noncanonical_column_names.ped`` file:

.. code-block:: bash

    ped2ped.py example_families_with_noncanonical_column_names.ped \
    --ped-family Family_id --ped-person Person_id --ped-dad Dad_id --ped-mom Mom_id \
    --ped-sex Sex --ped-status Status --ped-role Role \
    --ped-layout-mode generate -o example_families_from_noncanonical_column_names.ped

The `ped2ped.py` tool can also process pedigree files without headers. One such file is ``example_families_without_header.ped``.
In this case we have to map the column's index to a specific column name. The same way we mapped
'Family_id' to the family id column in the upper example, here we map the first column to family id
(Keep in mind the column indices begin from 0). See the example below:

.. code-block::

    ped2ped.py example_families_without_header.ped \
    --ped-no-header --ped-family 0 --ped-person 1 --ped-dad 2 --ped-mom 3 \
    --ped-sex 4 --ped-status 5 --ped-role 6 \
    --ped-layout-mode generate -o example_families_from_no_header.ped

Visualize a pedigree file into PDF file
#######################################

To visualize a pedigree file into a PDF file, containing drawings of the
family pedigrees you can use the `draw_pedigrees.py` tool.
To see its full functionality use::

    draw_pedigree.py --help

Notice that it shares a lot of common flags with the `ped2ped.py` tool. Similar to the `ped2ped.py` tool,
it can also process pedigree files with noncanonically named columns or without a header.

In addition to that, it has a ``--mode`` flag, which supports two values:

* `report`
    the tool will generate a family pedigree drawing for **each unique family structure** family

* `families`
    the tool will generate a family pedigree drawing for **every individual** family

To demonstrate how to use the `draw_pedigree.py` tool we will visualize the ``example_families.ped`` file:

.. code-block:: bash

    draw_pedigree.py example_families.ped -o example_families_visualization.pdf

This command outputs ``example_families_visualization.pdf`` file with the pedigree drawings.
