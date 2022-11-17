Getting Started with Preview Columns
####################################

For each study you can specify which columns are shown in the variants' table preview, as well as those which will be downloaded.

As an example we are going to redefine the `Frequency` column in the `comp_vcf`
study imported in the previous example.

Navigate to the `comp_vcf` study folder:

.. code::

    cd gpf_test/studies/comp_vcf


Edit the "genotype_browser" section in the configuration file ``comp_vcf.conf`` to looks like this:

.. code::

    [genotype_browser]
    enabled = true
    genotype.freq.name = "Frequency"
    genotype.freq.slots = [
        {source = "exome_gnomad_af_percent", name = "exome gnomad", format = "E %%.3f"},
        {source = "genome_gnomad_af_percent", name = "genome gnomad", format = "G %%.3f"},
        {source = "af_allele_freq", name = "study freq", format = "S %%.3f"}
    ]

This overwrites the definition of the default preview column `Frequency` to
include not only the gnomAD frequencies, but also the allele frequencies.
