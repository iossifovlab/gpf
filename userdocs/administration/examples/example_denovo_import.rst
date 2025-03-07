Example import of de novo variants from `Rates of contributory de novo mutation in high and low-risk autism families`
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Let us import de novo variants from the 
`Yoon, S., Munoz, A., Yamrom, B. et al. Rates of contributory de novo mutation
in high and low-risk autism families. Commun Biol 4, 1026 (2021). 
<https://doi.org/10.1038/s42003-021-02533-z>`_.

We will focus on de novo variants from the SSC collection published in the 
aforementioned paper.
To import these variants into the GPF system we need a list of de novo variants
and a pedigree file describing the families.
The list of de novo variants is available from 
`Supplementary Data 2 <https://static-content.springer.com/esm/art%3A10.1038%2Fs42003-021-02533-z/MediaObjects/42003_2021_2533_MOESM4_ESM.xlsx>`_.
The pedigree file for this study is not available. Instead, we have a list of
children available from `Supplementary Data 1 <https://static-content.springer.com/esm/art%3A10.1038%2Fs42003-021-02533-z/MediaObjects/42003_2021_2533_MOESM3_ESM.xlsx>`_.

Let us first export these Excel spreadsheets into CSV files. Let us say that the
list of de novo variants from the SSC collection is saved into a file named
``SupplementaryData2_SSC.tsv`` and the list of children is saved into a TSV file
named ``SupplementaryData1_Children.tsv``.

.. note:: 

    Input files for this example can be downloaded from 
    :download:`denovo-in-high-and-low-risk-papter.tar.gz <getting_started_files/denovo-in-high-and-low-risk-papter.tar.gz>`.

Preprocess the families data
____________________________

To import the data into GPF we need a pedigree file describing the structure
of the families. The ``SupplementaryData1_Children.tsv`` contains only the list
of children. There is no information about their parents. Fortunately for the
SSC collection it is not difficult to build the full families' structures from
the information we have. For the SSC collection if you have a family with ID
``<fam_id>``, then the identifiers of the individuals in the family are going to
be formed as follows:

* mother - ``<fam_id>.mo``;
* father - ``<fam_id>.fa``;
* proband - ``<fam_id>.p1``;
* first sibling - ``<fam_id>.s1``;
* second sibling - ``<fam_id>.s2``.

Another important restriction for SSC is that the only affected person in the 
family is the proband. The affected status of the mother, father and 
siblings are ``unaffected``.

Using all these conventions we can write a simple python script 
``build_ssc_pedigree.py``
to convert
``SupplementaryData1_Children.tsv`` into a pedigree file ``ssc_denovo.ped``:

.. code-block:: python

    """Converts SupplementaryData1_Children.tsv into a pedigree file."""
    import pandas as pd
    
    children = pd.read_csv("SupplementaryData1_Children.tsv", sep="\t")
    ssc = children[children.collection == "SSC"]
    
    # list of all individuals in SSC
    persons = []
    # each person is represented by a tuple:
    # (familyId, personId, dadId, momId, status, sex)
    
    for fam_id, members in ssc.groupby("familyId"):
        persons.append((fam_id, f"{fam_id}.mo", "0", "0", "unaffected", "F"))
        persons.append((fam_id, f"{fam_id}.fa", "0", "0", "unaffected", "F"))
        for child in members.to_dict(orient="records"):
            persons.append((
                fam_id, child["personId"], f"{fam_id}.fa", f"{fam_id}.mo",
                child["affected status"], child["sex"]))
    
    with open("ssc_denovo.ped", "wt", encoding="utf8") as output:
        output.write(
            "\t".join(("familyId", "personId", "dadId", "momId", "status", "sex")))
        output.write("\n")
    
        for person in persons:
            output.write("\t".join(person))
            output.write("\n")

If we run this script it will read ``SupplementaryData1_Children.tsv`` and
produce the appropriate pedigree file ``ssc_denovo.ped``.

Preprocess the variants data
____________________________

The ``SupplementaryData2_SSC.tsv`` file contains 255231 variants. To import so
many variants in in-memory genotype storage is not appropriate. For this
example we are going to use a subset of 10000 variants:

.. code-block:: bash

    head -n 10001 SupplementaryData2_SSC.tsv > ssc_denovo.tsv

Data import of ``ssc_denovo``
_____________________________

Now we have a pedigree file ``ssc_denovo.ped`` and a list of de novo
variants ``ssc_denovo.tsv``. Let us prepare an import project configuration
file ``ssc_denovo.yaml``:

.. code-block:: yaml

    id: ssc_denovo
    
    input:
      pedigree:
        file: ssc_denovo.ped
    
      denovo:
        files:
          - ssc_denovo.tsv
        person_id: personIds
        variant: variant
        location: location


To import the study we should run:

.. code-block:: bash

    import_tools ssc_denovo.yaml

and when the import finishes we can run the development GPF server:

.. code-block:: bash

    wgpf run

In the list of studies, we should have a new study ``ssc_denovo``.