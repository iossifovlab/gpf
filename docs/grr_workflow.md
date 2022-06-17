# Workflow for Management of Genomic Resources Repository

## Management of genomic resources

We assume that our genomic resources repositories are managed by a combination
of Git and DVC.

For any resource:

* all small files are managed by the Git

* all large resource files are managed using DVC and Git

### How to add a new resource to GRR

1. Create a directory appropriate for the resource. Let's assume this is
   a position score for the HG38 reference genome named `score9`. Then
   the directory should be something like this:

   ```
   hg38/scores/score9
   ```
  
2. Add all score resource files (score file and Tabix index) inside
   the created directory. Let's say these files are:

   ```
   score9.tsv.gz
   score9.tsv.gz.tbi
   ```

3. Add these files under version control:

    ```
    cd hg38/scores/score9
    dvc add score9.tsv.gz score9.tsv.gz.tbi
    ```
  
    These commands are going to create the `*.dvc` files for each of the
    resource files, that contain the md5 sum for the file, the size of the
    file and the file name.

    These `*.dvc` files should be added to the Git repository:
  
    ```
    git add score9.tsv.gz.dvc score9.tsv.gz.tbi.dvc
    git commit
    ```
  
    The resource files themselves should be pushed to the DVC remote:
  
    ```
    dvc push -r nemo
    ```
  
4. Configure the resource `hg38/scores/score9`. To this end create
   a `genomic_resource.yaml` file, that contains the position score
   configuration:

    ```yaml
    type: position_score
    table:
      filename: score9.tsv.gz
      format: tabix
        # defined by score_type
      chrom:
        name: chrom
      pos_begin:
        name: start
      pos_end:
        name: end
      # score values
    scores:
        - id: score9
          type: float
          desc: "score9"
          index: 3
      histograms:
      - score: score9
        bins: 100
        y_scale: "log"
        x_scale: "linear"
      default_annotation:
      attributes:
        - source: score9
          destination: score9
        meta: |
      ## score9
        TODO
    ```

   Add the configuration under version control:

   ```
   git add genomic_resource.yaml
   git commit
   ```

5. Build the score manifest. Run the command:

   ```bash
   grr_manage manifest . -r hg38/scores/score9
   ```
   This command should calculate the md5 sums for all resource files
   and store them into a resource manifest file named `.MANIFEST`.
 
   By default when the command finds `.dvc` files it will use them
   to get the `md5` sum for the corresponding files instead of computing it.

   If you want to suppress this behavior you can use the `--without-dvc`
   option:
 
   ```bash
   grr_manage manifest . -r hg38/scores/score9 --without-dvc
   ```
   or
   ```bash
   grr_manage manifest . -r hg38/scores/score9 -D
   ```

   The `--without-dvc` (`-D`) option will instruct the command to suppress usage
   of `.dvc` files and calculate `md5` sums of files when needed.

6. Build score histogram. Run the command:

   ```
   grr_manage histogram . -r hg38/scores/score9
   ```

   This command will check the resource to find
   all score histograms that are configured and will run the computation for 
   these histograms. For each configured score histogram three files are
   created. In the case of `hg38/scores/score9`, only one score histogram is
   configured. The three files that are stored are:

   * `histograms/score9.csv` that contains the histogram itself;

   * `histograms/score9.metadata.yaml` that contains the histogram metadata, e.g. 
     score min and max if they are not configured into the resource configuration,
     the histogram hash that is an md5 sum based on md5 sum of the score files and
     histogram configuration;

   * `histograms/score9.png` is a figure of the histogram for a quick inspection.

   In the end, this command will update the resource manifest file to include
   the histograms' files.

7. Add resource manifest and histogram files under Git version control

As an alternative to usage `manifest` and `histogram` commands, you can use a
`repair` command that combines the building of manifest and histograms of a
resource:

```bash
grr_manage repair . -r hg38/scores/score9
```

### Rebuild the manifests and histograms for all resources in a GRR

If you run the `repair` command without specifying a resource, it will
run on all resources of the repository:

```bash
grr_manage repair .
```

```
grr_manage repair --help
usage: grr_manage repair [-h] [--verbose] [-r RESOURCE] [-n] [-f] [-d] [-D] [--region-size REGION_SIZE] [-j JOBS] [--kubernetes] [--envvars [ENVVARS ...]] [--container-image CONTAINER_IMAGE] [--image-pull-secrets [IMAGE_PULL_SECRETS ...]] [--sge] [--dashboard-port DASHBOARD_PORT] [--log-dir LOG_DIR] repo_url

positional arguments:
  repo_url              Path to the genomic resources repository

optional arguments:
  -h, --help            show this help message and exit
  --verbose, -v, -V
  -r RESOURCE, --resource RESOURCE
                        specifies a resource whose manifest/histograms we want to rebuild; if not specified the command will run on all resources in the repository
  -n, --dry-run         only checks if the manifest and/or histograms update is needed whithout actually updating it
  -f, --force           ignore resource state and rebuild manifest and histograms
  -d, --with-dvc        use '.dvc' files if present to get md5 sum of resource files
  -D, --without-dvc     calculate the md5 sum if necessary of resource files; do not use '.dvc' files to get md5 sum of resource files
  --region-size REGION_SIZE
                        split the resource into regions with region length for parallel processing
  -j JOBS, --jobs JOBS  Number of jobs to run in parallel. Defaults to the number of processors on the machine
  --kubernetes          Run computation in a kubernetes cluster
  --envvars [ENVVARS ...]
                        Environment variables to pass to kubernetes workers
  --container-image CONTAINER_IMAGE
                        Docker image to use when submitting jobs to kubernetes
  --image-pull-secrets [IMAGE_PULL_SECRETS ...]
                        Secrets to use when pulling the docker image
  --sge                 Run computation on a Sun Grid Engine cluster. When using this command it is highly advisable to manually specify the number of workers using -j
  --dashboard-port DASHBOARD_PORT
                        Port on which to run Dask Dashboard
  --log-dir LOG_DIR     Directory where to store SGE worker logs
```

### How to make a small change in a resource in GRR

Let's say we want to change the description of a `hg38/scores/score9` resource.

1. Clone the Git GRR repository. Since we do not change any of the large resource
   files we do not need to check out the DVC repository.

2. Edit the `genomic_resource.yaml` file and rerun the `manifest` command:

   ```
   grr_manage manifest . -r hg38/scores/score9
   ```

   This command should update the `genomic_resource.yaml` entry into
   the resource `.MANIFEST` file.

4. Check that histograms should not be rebuilt:

   ```
   grr_manage histogram . -r hg38/scores/score9 --dry-run
   ```

   If the previous command reports that any of the resource histograms need
   rebuilding you should refer to the next section of the document.

5. Add the `.MANIFEST` resource file to the Git repository.


### How to make a big change in a resource in GRR

Let's say we need to change any of the large resource files -- e.g. rebuild the
score Tabix index. To do this change we need to:

1. Clone the Git GRR repository.

2. Check out the DVC files for the resource you plan to update.

   ```bash
   dvc fetch -r nemo ht38/scores/score9/score9.tsv.gz.dvc ht38/scores/score9/score9.tsv.gz.tbi.dvc
   dvc checkout ht38/scores/score9/score9.tsv.gz.dvc ht38/scores/score9/score9.tsv.gz.tbi.dvc
   ```

   Alternatively, you can pull all DVC files by running:

   ```
   dvc pull -r nemo
   ```


3. After changing the score resource files add the updated score files
   under DVC version control:

   ```   
   dvc add score9.tsv.gz score9.tsv.gz.tbi
   ```
   
   and add `*.dvc` files into the Git repo.

4. Run the `manifest` command:

   ```
   grr_manage manifest . -r hg38/scores/score9
   ```

5. Rebuild the histograms:

   ```
   grr_manage histogram . -r hg38/scores/score9
   ```

6. Add resource manifest and histogram files under Git version control

### Notes on GRR histogram command

Note that the GRR management `histogram` command expects that the manifest of the
resource is in sync with the resource files. Before running the `histogram` command
you should always run the `manifest` command to ensure, that the `.MANIFEST`
of the resource is up to date.

### GRR resource files state

For each GRR resource file the `manifest` command stores:

* name of the resource file;
* md5 sum of the resource file;
* size of the resource file;
* timestamp of the resource file.

This state information is stored in a file inside the resource state directory
 `.grr`. This state directory
should be git ignored and should not be put into the Git repository.

For each resource file (e.g. `hg38/scores/score9/score9.tsv.gz`) the `manifest`
command creates a state file `.grr/hg38/scores/score9/score9.tsv.gz.state`
that contains the state info:

```
filename: score9.tsv.gz
md5: 978ad036fe7f3e0b822485c8ee8285de
size: 3153512062
timestamp: '2022-06-07T06:53:50+00:00'
```

### Optimizations based on the GRR resource file state

When the GRR management `manifest` command is run it should
recalculate the md5 sum for each resource file.

Before calculating the md5 sums for a given resource file,
the `manifest` command checks the state of this resource file.

If the state timestamp and size coincide with the size and timestamp
of the resource file, then the md5 sum is not recomputed and the one
from the state is used.




## Abstract

At the moment genomic resource's manifest contains the last modification
timestamp for each resource file.

These timestamps create several problems with managing genomic resources
repositories:

* to keep track of changes in genomic resources we use Git but Git does not
  keep the modification timestamps of files, so when the GRR has been cloned
  the modification timestamps of the files and timestamps stored in the
  manifest are different;

* to version control the large resource files we are using DVC but DVC 
  does not keep the modification timestamps of files;

* when GPF caches a resource file it manipulates its modification timestamp
  to match the manifest timestamp; this operation is supported for the local
  filesystem (directory repository) but is not supported on S3
  (S3 repository);

* using timestamps does not guarantee that the file is not changed;
  timestamps could be used only for optimization of some long-running
  operations.

### Proposal

* Remove timestamps from the manifest.

* **Optimization**: consider storing timestamps and other identification information
  about resource files in a special hidden GRR directory/file; (check `.dvc/tmp/md5s`
  in [DVC internal files](https://dvc.org/doc/user-guide/project-structure/internal-files)).

## Introduction

Each genomic resource consists of a configuration
file `genomic_resource.yaml` and a set of resource files
that are located together in a directory subtree. Check
[GPF Genomics Resources Repository (GRR)](`https://www.iossifovlab.com/distribution/public/genomic-resources-repository/`)
for examples.

The GPF Genomics Resources Repository (GRR) is under version control
using a combination of Git and Dvc for managing large resource files.

The GPF system can use the genomic resources using several workflows:

* using direct access from the public GRR without downloading resources
  locally;

* using GPF caching repository that will download resources before using
  them;

* using local resources managed by a local GRR.

The most common (and recommended) case is **caching the resources locally**
using the GPF caching repository.

To manage the consistency of copies of genomic resources the GPF uses a
genomic resource manifest file. The manifest file contains entries for
each file of the resource that contain the following data:

* file name relative to the genomic resource directory;

* file size (in bytes);

* md5 sum of the file;

* the modification time of the file (as ISO formatted date-time).

At the moment GRR uses the file's modification time to make decisions:

* check if the resource is changed and needs recalculation of md5sum;

* check if the resource is changed and needs recalculation of statistics/histograms;

* check if the cached resource is the same as the resource from GRR or needs an update;

* etc.

## Resource Caching

At the moment when GPF uses a caching genomics repository the steps performed
by the GPF are:

* the client requests a resource with a specified `ID`;

* the caching GRR checks if this resource is available at the remote GRR; 

* if the resource with `ID` is not found in the remote GRR the repository
  returns `None` that signals the client that this resource is missing;

* otherwise, the caching GRR gets the manifest from the remote GRR and compares it
  with the manifest in caching GRR;

* if the local manifest is missing the caching GRR stores it and returns the 
  cached resource;

* otherwise, if the local manifest is equal to the remote manifest the caching
  GRR returns the cached resource;

* otherwise, if the local manifest and remote manifest are different, the caching
  GRR cleans the cached resource files, stores the remote manifest and returns
  the cached resource.

When the client wants to use a file from the cached resource `ID`, the steps
performed by the GPF are:

* the caching GRR checks if the cached resource already has the requested
  resource file;

* if the requested resource file is cached, then it is opened and returned to
  the client;

* otherwise, the caching GRR copies the resource file in the cache opens it
  and returns the opened file to the client.


## Problems with the Timestamps

### Git and DVC do not keep the timestamps of the files

To work around this problem we have implemented a subcommand `checkout` 
to the `grr_manage` tool that
updates all resource files modification timestamps to match the 
timestamps from the resource manifest file.

This approach works for the local filesystem (directory repository)
but could not be transferred to the S3 repository.

### Modification timestamps could not be manipulated on S3

Since we heavily rely on timestamps and their manipulation we could not make 
a proper writeable S3 repository. This will limit the usability of the 
GRR for processing genomic resources on clusters.

## Proposed Solution

**Stop storing modification timestamps in resources' manifest files.**

### Interaction with Git and DVC

**Removing timestamps from manifests is going to make version control of
genomic resources much simpler.**
Since resources' manifest files do not contain timestamps we can rely
on Git and DVC to maintain the integrity of resource files.

#### Optimizations

Generally, modification timestamps were used only for optimization for some
`grr_manage` commands. We could keep these optimizations and probably add
new optimization.

* We can store timestamps in a GRR internal state file(s). Check `.dvc/tmp/md5s`
  in [DVC internal files](https://dvc.org/doc/user-guide/project-structure/internal-files)
  for ideas.
  GRR manage command could use this internal state to optimize decisions for indexing given
  resources and for calculating the resource statistics

* We can use `.dvc` files for large resource files to skip the calculation of md5 sums.


### Interaction with caching

While caching resource files the caching GRR calculates its md5sum
to validate the copy with the manifest md5sum value. If the calculated
md5sum does not match the manifest md5sum value the copy of the resource
file is removed and an exception is raised.

So we don't need the timestamp
to decide the validity of the copied resource files.

When a resource file is in the cached resource this means that its md5sum
is equal to the md5sum value in the resource manifest.

When accessing a cached resource, the first step of the caching GRR is to get
the remote resource manifest and compare it to the cached manifest. If the
remote manifest and cached manifest are different, the cached resource files that 
are different are removed from the cached resource, the remote manifest is
stored in the cached GRR and after that, the cached resource is used. See
[Resource Caching](#resource-caching)

**We do not need timestamps for the implementation of caching.**


