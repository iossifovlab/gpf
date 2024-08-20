
Getting Started with Enrichment Tool
####################################

For studies that include de Novo variants, you can enable the enrichment tool UI.
As an example, let us enable it for the already imported
`iossifov_2014` study.

Go to the directory where the configuration file of the `iossifov_2014`
study is located::

    cd gpf_test/studies/iossifov_2014

Edit the study configuration file ``iossifov_2014.conf`` and add the following section in the end of the file::

    [enrichment]
    enabled = true

Restart the GPF web server::

    wdaemanage.py runserver 0.0.0.0:8000

Now when you navigate to the iossifov_2014 study in the browser,
the Enrichment Tool tab will be available.
