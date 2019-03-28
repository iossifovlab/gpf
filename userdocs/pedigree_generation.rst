Pedigree Generation Guide
=========================


Brief outline
#############

Starting off with a pedigree file that contains information about families and their individuals, we will run the file through two tools - the first one will add a column to the pedigree file - a layout column that contains the coordinates of each individual in the pedigree drawing that will be produced - and the second tool will generate a PDF file which contains the pedigree drawing, as well as some optional info.

This guide covers most cases; some specific notes regarding usage with the SVIP study are given at the end.


Prerequisites
#############

You will need a pedigree file (usually found with a .ped extension), which is a text file with delimiter-separated values (comma, tab, etc.), that contains the following columns:

:Family ID: The values in this column must contain valid family IDs.
:ID: IDs for separate individuals.
:Father ID: A column that specifies the ID of the individual's father.
:Mother ID: A column that specifies the ID of the individual's mother.
:Sex: The sex of the individual.
:Status: A column that specifies the status of the individual - whether he is affected or not.
:Role: The role of the individual within his family.


Adding the layout column
########################

You will need to use the tool 'save_pedigree.py', which can be found in 'DAE/tools'.

The tool has a '-h' or '--help' option, which brings out a list of possible arguments and brief descriptions.

For most cases, the default values should be sufficient, but it is recommended to look through and make sure.

.. code-block:: bash

    save_pedigree.py inital_pedigree_file.ped -o output_pedigree_file.ped


Drawing the pedigree
####################

Next, you will need the tool 'draw_pedigree', which can be found again in 'DAE/tools'.

As before, this tool has a help argument detailing its arguments.

You will need to use the output pedigree file from the previous step.

.. code-block:: bash

    draw_pedigree.py pedigree_file_with_layout.ped -o pedigree_drawing.pdf


Some notes regarding SVIP
#########################

Generating the pedigree layout and drawing for SVIP involves more steps, and problems may occur during the process. 

Additionally, a few additional scripts are used to prepare the pedigree data, before using the tools specified above.

Preparing the pedigree data
***************************

SVIP's initial pedigree file must be expanded with additional individuals in order to correctly form some families. (TODO, where do we get the additional individuals from? is the reason accurate?)

Following that, a script is ran to connect individuals with their parents from the additional individuals we added.

Next, we need to replace the roles' names with those used by the GPF system, using another script.

At this point, the save_pedigree tool can be ran.

Following this, we run a script that adds a '-' status to generated individuals.

The pedigree file has now been prepared and the draw_pedigree tool can be ran.

Potential errors during layout generation
*****************************************

Although uncommon, errors can occur during layout generation (save_pedigree.py tool). This is usually caused due to missing individuals in families.

The pedigree file will be generated, but some entries in the layout column will contain an error message instead of coordinates. Unfortunately, the solution to this is manual insertion of layout coordinated.
