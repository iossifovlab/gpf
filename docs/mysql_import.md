# Import of transmitted variants into MySQL database

When transmitted variants are imported into MySQL database they are located 
into three tables:
```
+-------------------------------+
| transmitted_summaryvariant    |
| transmitted_geneeffectvariant |
| transmitted_familyvariant     |
+-------------------------------+
```
* `transmitted_summaryvariant` table contains summary variants data
* `transmitted_geneeffectvariant` table contains effect types for each 
summary variant
* `transmitted_familyvariant` table contains family specific information for
each family and summary variant

## Data import into MySQL

To import transmitted variants into MySQL database we use a two step process:

* Using `myisam_transmitted_build.py` tool we prepare SQL statements that
import all transmitted variants into given MySQL database. The result of this
operation are three files containing SQL create and insert statements for
data into MySQL database - one file for each of the tables summary variants,
effect type and family variants.

* Using `myisam_transmitted_import.py` we import the prepared SQL statements
into existing MySQL database.


## Usage of `myisam_transmitted_build.py`

The `myisam_transmitted_build.py` support help page that can be shown using
`-h` option:

```
myisam_transmitted_build.py -h
usage: myisam_transmitted_build.py [-h] [-s] [-e] [-f] [-a] [-o OUTDIR] [-V]
                                   [-S study_name] [-F familes]
                                   [-T TRANSMITTEDFILE] [-M TOOMANYFILE]

myisam_transmitted_build -- prepares MySQL statements for given transmitted study.
2015-10-15
USAGE

optional arguments:
  -h, --help            show this help message and exit
  -s, --summary         builds summary vartiants table [default: False]
  -e, --geneeffect     builds gene effect variants table [default: False]
  -f, --family          builds family variants table [default: False]
  -a, --all             builds all variants table [default: False]
  -o OUTDIR, --outdir OUTDIR
                        output directory where to store SQL files.[default: .]
  -V, --version         show program's version number and exit
  -S study_name, --studyname study_name
                        study name to process [default: None]
  -F familes, --familiesfile familes
                        study families filename
  -T TRANSMITTEDFILE, --transmittedfile TRANSMITTEDFILE
                        transmitted variants base file name
  -M TOOMANYFILE, --toomanyfile TOOMANYFILE
                        transmitted variants family variants file name
```

To start the `myisam_transmitted_build.py` one need to supply following
required argments:

* `-F` or `--familiesfile` should specify a file, containing
families data in families simple format
* `-T` or `--transmittedfile` should specify a file,
containing transmitted variants
* `-M` or `--toomanyfile` should specify TOOMANY file with family variants.
* `-o` or `--outdir` should specify a directory where one wants to store the
output variables
* `-S` or `--studyname` should specify a name for study that one works with.

There are some flags that are optional and can be use to specify which part of
the we need to build:
* `-s` or `--summary` creates only the file for summary variants
* `-e` or `--geneeffect` create only the file with effect types for all summary
variants
* `-f` or `--family` creates only the file for family variants
* `-a` or `--all` creates all the files.


Example invocation for `

## Usage of `myisam_transmitted_import.py`


```
myisam_transmitted_import.py -h
usage: myisam_transmitted_import.py [-h] [-V] [-s SUMMARY_FILENAME]
                                    [-f FAMILY_FILENAME]
                                    [-e GENE_EFFECT_FILENAME] [-H HOST]
                                    [-P PORT] [-p PASSWORD] [-u USER]
                                    [-D DATABASE] [-S STUDY]

myisam_transmitted_import -- import transmitted variants into MySQL
2015-10-15
USAGE

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -s SUMMARY_FILENAME, --summary SUMMARY_FILENAME
  -f FAMILY_FILENAME, --family FAMILY_FILENAME
  -e GENE_EFFECT_FILENAME, --gene_effect GENE_EFFECT_FILENAME
  -H HOST, --host HOST  MySQL host
  -P PORT, --port PORT  MySQL port
  -p PASSWORD, --password PASSWORD
                        MySQL password
  -u USER, --user USER  MySQL user
  -D DATABASE, --database DATABASE
                        MySQL database
  -S STUDY, --study STUDY
                        study name to process [default: None]
```

