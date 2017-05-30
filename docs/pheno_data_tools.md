# Phenotype Data Tools

## Import Phenotype Data into GPF System

The tool used to import phenotype data into GPF system is `pheno2DAE.py`. 

### Phenotype measurements data format

The phenotype data imported into the GPF system should be stored into
collection of `CSV` files. 

Each `CSV` file contains collection of measurements, organized in
following format: the first column into the `CSV` file should contain the individuals IDs
followed by columns for different phenotype measurements. One such `CSV` file
is called *instrument* and columns into this file are called *measures*.


### The `pheno2DAE.py` help
The tool has a help info that can be shown using `-h` option on the command line:

```
pheno2DAE.py -h
usage: pheno2DAE.py [-h] [-v] [-V] [-i path] [-f path] [-o filename]
                    [-C CONTINUOUS] [-O ORDINAL] [-A CATEGORICAL]
                    [-I INDIVIDUALS]

pheno2DAE -- prepares a DAE pheno DB cache

USAGE

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         set verbosity level [default: None]
  -V, --version         show program's version number and exit
  -i path, --instruments path
                        directory where all instruments are located
  -f path, --families path
                        file where families description are located
  -o filename, --output filename
                        ouput file
  -C CONTINUOUS, --continuous CONTINUOUS
                        minimal count of unique values for a measure to be
                        classified as continuous (default: 15)
  -O ORDINAL, --ordinal ORDINAL
                        minimal count of unique values for a measure to be
                        classified as ordinal (default: 5)
  -A CATEGORICAL, --categorical CATEGORICAL
                        minimal count of unique values for a measure to be
                        classified as categorical (default: 2)
  -I INDIVIDUALS, --individuals INDIVIDUALS
                        minimal number of individuals for a measure to be
                        considered for classification (default: 20)
```

### Typical invocation of `pheno2DAE.py`

To start `pheno2DAE.py` one should pass some required parameters:

* using `-f` the user should supply a pedigree file for families tha should be
imported into the system

* using `-o` option the user should pass the name of the output file where
the processed phenotype data should be stored

* using `-i` option the user could pass a directory with `CSV` files, containing
phenotype measures

Example usage:
```
pheno2DAE.py -f nuc_svip.ped -i SVIP_16p11.2/ -o vip.db
```

As a result all *instruments* from `SVIP_16p11.2/` directory are stored into
`vip.db` file.


### Phenotype measures classification

During import of phenotype measurements into GPF system the `pheno2DAE.py`
classifies each measure into three different categories: *continuous*, *ordinal*
and *categorical*.

* To import a measure into the phenotype DB it has to have minimal number of
measurements. If given measure is applied to small number of individuals
it is not imported into the phenotype DB. The minimal number of individuals to
which a measure should be applied is specified in `individuals` parameter
of `phenot2DAE.py`. The default value of `individuals` parameter is 20.

* When the values of a measure are not numerical, the measure is classified as
*categorical*.

* When the values of a measure are numerical, then the classification depends on
the number of unique values of the measure. 

    * To classify a measure as *continuous* the number of unique values should be 
    greater than or equal to parameter `continuous`. Default value of `continuous` 
    parameter is `15`.
    
    * When the number of unique values of a measure is less than `continuous` 
    parameter, but greater than or equal to `ordinal` parameter, the measure is 
    classified as `ordinal`. The default value of `ordinal` parameter is `5`.
    
    * When the number of unique values of a measure is less than `ordinal` parameter,
    but greater than or equal to `categorical` parameter, the measure is classified
    as `categorical`. The default value of `categorical` is `2`.


### Configure phenotype DB into the GPF system

The file prepared with `pheno2DAE.py` tool could be configured to become 
accessible through GPF system. To this end one should edit `phenoDB.conf` file
from the GPF system data directory.

Example configuration is:

```
[pheno]
dbs=vip

[cache_dir]
dir=%(wd)s/pheno/cache

[vip]
cache_file=vip.db
age=measure.eval_age_months
nonverbal_iq=diagnosis_summary:best_nonverbal_iq

```

* in section `[pheno]` variable `dbs` contains a comma separated list of all
phenotype DBs configured into the
system. Each configured phenotype DB has a separed configuration section,
containing the phenotype DB configuration itself.
In the example only one phenotype database is configured - `vip`. 

* the section `[cache_dir]` configures default directory where phenotype DB files
are stored.
* the section `[vip]` contains the configuration of phenotype DB `vip`. 
    * `cache_file` - the file prepared with `pheno2DAE.py` tool for the specified
    phenotype DB
    * `age` and `nonverbal_iq` - several GPF tools explore corellation between
    phenotype measures and the age and non-verbal IQ. To support this functionality
    we need to configure the phenotype measures that correspond to the *age* and 
    *non-verbal IQ*.


## Phenotype Browser Data Preparation

Phenotype browser displays various statistics of phenotype DB measures. Most
of the data displayed by the phenotype browser is prepared by 
`pheno_browser_cache` tool.

### Phenotype browser activation
When a dataset has specified `phenoDB` and `phenotypeBrowser` variables,
then the phenotype browser tool becomes active in the user interface of
GPF system:

```
...
[dataset.VIP]
...
phenoDB=vip
phenotypeBrowser=yes
...
```

### Phenotype browser configuration

Configuration of phenotype browser is specified into Django settings 
`wdae/settings.py`. One should specify two variables:

* `PHENO_BROWSER_CACHE` - a directory where the phenotype browser cache is
located

* `PHENO_BROWSER_BASE_URL` - a base URL for serving phenotype browser
figures

### Generation of phenotype browser figures and resources

To prepare phenotype browser figures and other data one should use
`pheno_browser_cache` Django management command. The available help
page could be invoked using `-h` option:
```
./manage.py pheno_browser_cache -h
usage: manage.py pheno_browser_cache [-h] [--version] [-v {0,1,2,3}]
                                     [--settings SETTINGS]
                                     [--pythonpath PYTHONPATH] [--traceback]
                                     [--no-color] [-f] [-p PHENO]

Rebuild pheno browser static figures cache

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -v {0,1,2,3}, --verbosity {0,1,2,3}
                        Verbosity level; 0=minimal output, 1=normal output,
                        2=verbose output, 3=very verbose output
  --settings SETTINGS   The Python path to a settings module, e.g.
                        "myproject.settings.main". If this isn't provided, the
                        DJANGO_SETTINGS_MODULE environment variable will be
                        used.
  --pythonpath PYTHONPATH
                        A directory to add to the Python path, e.g.
                        "/home/djangoprojects/myproject".
  --traceback           Raise on CommandError exceptions
  --no-color            Don't colorize the command output.
  -f, --force           Force recalculation of static resources
  -p PHENO, --pheno PHENO
                        Specify with pheno db to use. By default works on all
                        configured pheno DBs
```

The important parameters are:

* `-f`, `--force` - force generation of static resources. By default the tool
checks if there are any changes in phenotype databases and if there are no
changes it does nothing. The tool will generate static resources only if
there is a change in some of phenotype database.

* `-p PHENO_DB`, `--pheno PHENO_DB` - specifies phenotype DB for which the
static resources should be generated. By default the tool generates static 
resources for all phenotype databases specified in `phenoDB.conf` file.