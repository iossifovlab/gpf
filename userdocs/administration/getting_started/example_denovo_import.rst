Example import of real data
###########################
  
Source of the data
++++++++++++++++++

Let us import de novo variants from the 
`Yoon, S., Munoz, A., Yamrom, B. et al. Rates of contributory de novo 
mutation in high and low-risk autism families. 
Commun Biol 4, 1026 (2021). <https://doi.org/10.1038/s42003-021-02533-z>`_

We will focus on de Novo variants from the SSC collection published in the 
aforementioned paper.

To import these variants into the GPF system, we need 
a pedigree file describing the families and 
a list of de novo variants.

The pedigree file for this study is not available. Instead, we have a list 
of children available from 
`Supplementary Data 
1. <https://pmc.ncbi.nlm.nih.gov/articles/instance/8410909/bin/42003_2021_2533_MOESM3_ESM.xlsx>`_

The list of SNP and INDEL de novo variants is available from 
`Supplementary Data 
2. <https://pmc.ncbi.nlm.nih.gov/articles/instance/8410909/bin/42003_2021_2533_MOESM4_ESM.xlsx>`_

The list of CNV de novo variants is available from
`Supplementary Data 
4. <https://pmc.ncbi.nlm.nih.gov/articles/instance/8410909/bin/42003_2021_2533_MOESM6_ESM.xlsx>`_


.. note:: 

    All the data files needed for this example are available in the
    `gpf-getting-started <https://github.com/iossifovlab/gpf-getting-started.git>`_
    repository under the subdirectory ``example_imports/denovo_and_cnv_import/input_data``.


Preprocess the Family Data
++++++++++++++++++++++++++

The list of children in ``Supplementary_Data_1.tsv.gz`` contains a lot of data 
that is not relevant for the import. 
We are going to use only the first five 
columns from that file that look as follows:

.. code-block:: bash
    zcat Supplementary_Data_1.tsv.gz | head | cut -f 1-5 | less -S -x 20 


    collection          familyId            personId            affected status     sex
    SSC                 11000               11000.p1            affected            M
    SSC                 11000               11000.s1            unaffected          F
    SSC                 11003               11003.p1            affected            M
    SSC                 11003               11003.s1            unaffected          F
    SSC                 11004               11004.p1            affected            M
    SSC                 11004               11004.s1            unaffected          M
    SSC                 11006               11006.p1            affected            M
    SSC                 11006               11006.s1            unaffected          M
    SSC                 11008               11008.p1            affected            M


* The first column contains the collection. This study contains data from SSC 
  and AGRE collections. We are going to import only variants from the 
  SSC collection.

* The second column contains the family ID.

* The third column contains the person's ID.

* The fourth column contains the affected status of the individual.
  
* The fifth column contains the sex of the individual.

We need a pedigree file describing the family's structure to import the data 
into GPF. The `SupplementaryData1_Children.tsv.gz` contains only the  children; 
it does not include information about their parents. 
Fortunately for the SSC collection, it is not difficult to build the whole 
families' structures from the information we have. 

So, before starting the work on the import, we need to preprocess the 
list of children and transform it into a pedigree file.

For the SSC collection, if you have a family with ID`<fam_id>`, then the 
identifiers of the individuals in the family are going to be formed as follows:

* mother - ``<fam_id>.mo``;
  
* father - ``<fam_id>.fa``;
  
* proband - ``<fam_id>.p1``;
  
* first sibling - ``<fam_id>.s1``;
 
* second sibling - ``<fam_id>.s2``.  

Another essential restriction for SSC is that the only affected person in the 
family is the proband. The affected status of the mother, father, and 
siblings is unaffected.

Having this information, we can use the following `Awk` script to transform 
the list of children into a pedigree:

.. code:: bash
    gunzip -c Supplementary_Data_1.tsv.gz | awk '
        BEGIN {
            OFS="\t"
            print "familyId", "personId", "dadId", "momId", "status", "sex"
        }
        $1 == "SSC" {
            fid = $2
            if( fid in families == 0) {
                families[fid] = 1
                print fid, fid".mo", "0", "0", "unaffected", "F"
                print fid, fid".fa", "0", "0", "unaffected", "M"
            }
            print fid, $3, fid".fa", fid".mo", $4, $5
        }' > ssc_denovo.ped


If we run this script, it will read ``Supplementary_Data_1.tsv.gz`` and produce 
the appropriate pedigree file ``ssc_denovo.ped``.

The resulting pedigree file is also available in the 
`gpf-getting-started <https://github.com/iossifovlab/gpf-getting-started.git>`_
repository under the subdirectory 
``example_imports/denovo_and_cnv_import/input_data``.

.. literalinclude:: gpf-getting-started/example_imports/denovo_and_cnv_import/input_data/ssc_denovo.ped
    :tab-width: 15
    :lines: 1-21

Preprocess the SNP and INDEL de Novo variants
+++++++++++++++++++++++++++++++++++++++++++++

The `Supplementary_Data_2.tsv.gz` file contains 255232 variants. 
For the import, we will need columns four and nine from this file:

.. code-block:: bash

    gunzip -c Supplementary_Data_2.tsv.gz | head | cut -f 4,9 | less -S -x 20

    personIds           variant in VCF format
    13210.p1            chr1:184268:G:A
    12782.s1            chr1:191408:G:A
    12972.s1            chr1:271774:AG:A
    12420.p1            chr1:484721:AG:A
    12518.p1,12518.s1   chr1:691130:T:C
    13882.p1            chr1:738645:C:G
    14039.s1            chr1:819832:G:T
    13872.p1            chr1:824001:AAAAT:A


Using the following `Awk` script, we can transform this file into easy to 
import list of de Novo variants:

.. code:: bash

    gunzip -c Supplementary_Data_2.tsv.gz | cut -f 4,9 | awk '
        BEGIN{
            OFS="\t"
            print "chrom", "pos", "ref", "alt", "person_id"
        }
        NR > 1 {
            split($2, v, ":")
            print v[1], v[2], v[3], v[4], $1
        }' > ssc_denovo.tsv


The resulting pedigree file is also available in the 
`gpf-getting-started <https://github.com/iossifovlab/gpf-getting-started.git>`_
repository under the subdirectory 
``example_imports/denovo_and_cnv_import/input_data``.

.. literalinclude:: gpf-getting-started/example_imports/denovo_and_cnv_import/input_data//ssc_denovo.tsv     
    :tab-width: 15
    :lines: 1-20


Caching GRR
+++++++++++

Now we are about to import 255K variants. During the import, the GPF system
will annotate these variants using the GRR resources from our 
`public GRR. <https://grr.iosiffovlab.com>`_

For small studies with few variants this approach is quite convienient.
However, for larger studies, it is better to cache the GRR resources locally.

To do this, we need to configure the GRR to use a local cache. Create a file
named ``.grr_definition.yaml`` in your home directory with the following content:

.. code-block:: yaml

    id: "seqpipe"
    type: "url"
    url: "https://grr.iossifovlab.com"
    cache_dir: "<path_to_your_cache_dir>"

To download all the resources needed for out ``minimal_instance``, run
the following command from ``gpf-getting-started`` directory:

.. code-block:: bash

    grr_cache_repo -i minimal_instance/gpf_instance.yaml

.. note::

    The ``grr_cache_repo`` command will download all the resources needed for
    the GPF instance. This may take a while, depending on your internet 
    connection and the number of resources you configuration require.

    The resources will be downloaded to the directory specified in the 
    ``cache_dir`` parameter of the ``.grr_definition.yaml`` file.

    For the ``gpf-getting-started`` repository, the resources that will be 
    downloaded:

    * ``hg38/genomes/GRCh38-hg38``

    * ``hg38/gene_models/MANE/1.3``

    * ``hg38/variant_frequencies/gnomAD_4.1.0/genomes/ALL``

    * ``hg38/scores/ClinVar_20240730``

    The total size of the downloaded resources is about 15 GB.


Data Import of ``ssc_denovo``
+++++++++++++++++++++++++++++

Now we have a pedigree file, ``ssc_denovo.ped``, and a list of de novo 
variants, ``ssc_denovo.tsv``. Let us prepare an import project configuration 
file, ``ssc_denovo.yaml``:

.. literalinclude:: gpf-getting-started/example_imports/denovo_and_cnv_import/input_data/ssc_denovo.yaml

  
To import the study, we should run:

.. code:: bash

    time import_genotypes -v -j 1 ssc_denovo.yaml

    real    10m23.760s
    user    10m2.447s
    sys     0m9.471s

When the import finishes, we can run the development GPF server:


.. code:: bash

    wgpf run

In the home page of the GPF instance we should have the new study ``ssc_denovo``.
If you follow the link to the study, and choose the `Genotype Browser` tab, you 
will be able to query the variants.

.. figure:: getting_started_files/ssc_denovo_genotype_browser.png

    Genotype browser for the SSC de novo variants.
