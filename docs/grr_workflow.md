# Workflow for Management of Genomic Resources Repository

## Abstract

At the moment genomic resource's manifest contains last modification
timestamp for each resource file.

These timestamps create several problems with managing genomic resources
respositories:

* to keep track of changes in genomic resources we use Git but Git does not
  keep the modification timestamps of files; so when the GRR is cloned
  the modification timestamps of the files and timestamps stored in the
  manifest are different;

* to version control the large resource files we are using DVC but DVC 
  does not keep the modification timestamps of files;

* when GPF caches a resource file it manipulates it's modification timestamp
  to match the manifest timestamp; this operation is supported for local
  filesystem (directory repository), but is not supported on S3
  (S3 repository);

* using timestamps does not garuantee the the file is not changed or not
  changed; timestamps could be used only for optimization of some long running
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
using combination of Git and Dvc for managing large resource files.

The GPF system can use the genomic resources using several workflows:

* using direct access from the public GRR without downloading resources
  locally;

* using GPF caching repository that will download resources before using
  them;

* using local resources managed by a local GRR.

The most common (and recommended) case is **caching the resources locally**
using the GPF caching repository.

To manage the consistency of copies of genomic resources the GPF uses 
genomic resource manifest file. The manifest file contains entries for
each file of the resource that contain following data:

* file name relative to the genomic resource directory;

* file size (in bytes);

* md5 sum of the file;

* modification time of the file (as ISO formatted date-time).

At the moment GRR uses file's modification time to make decisions:

* check if the resource is changed and needs recalculation of md5sum;

* check if the resource is changes and needs recalculation of statistics/histograms;

* check if the cached resource is the same as the resource from GRR or needs update;

* etc.

## Resource Caching

At the moment when GPF uses a caching genomics repository the steps performed
by the GPF are:

* the client requests a resource with a specified `ID`;

* the caching GRR checks if this resource is available at the remote GRR; 

* if the resource with `ID` is not found in the remote GRR the repository
  returns `None` that signals the client that this resource is missing;

* otherwise the caching GRR gets the manifest from remote GRR and compares it
  with the manifest in caching GRR;

* if the local manifest is missing the caching GRR stores it and returns the 
  cached resource;

* otherwise, if the local manifest is equal to the remote manifest the caching
  GRR returns the cached resource;

* otherwise, if the local manifest and remote manifest are different, the caching
  GRR cleans the cached resource files, stores the remote manifest and returns
  the cached resource.

When the client whant to use a file from the cached resource `ID`, the steps
performed by the GPF are:

* the caching GRR checks if the cached resource olready has the requested
  resource file;

* if the requested resource file is cached, then it is opened and returned to
  the client;

* otherwise, the caching GRR copies the resource file in the cache, opens it
  and returns the opened file to the client.


## Problems with the Timestamps

### Git and DVC does not keep the files timestamps

To work around this problem we have implemented a subcommand `checkout` 
to the `grr_manage` tool that
updates all resource files modification timestamps to match the 
timestamps from the resource manifest file.

This approach works for local filesystem (directory repository)
but could not be transferred to S3 repository.

### Modification timestamps could not be manipulated on S3

Since we haviely rely on timestamps and it's manipulation we could not
make proper writeble S3 repository. This will limit usability of the 
GRR for processing genomic resources on clusters.

## Proposed Solution

**Stop storing modification timestamps in resources' manifest files.**

### Interaction with Git and DVC

**Removing timestamps from manifests is going to make version control of
genomic resources much much simpler.**
Since resources' manifest files does not contain timestamps we can rely
on Git and DVC to maintain the integrety of resource files.

#### Optimizations

Generally modification timestamps were used only for optimization for some
`grr_manage` commands. We could keep these optimizations and probably add
new optimization.

* We can store timestamps in an GRR internal state file(s). Check `.dvc/tmp/md5s`
  in [DVC internal files](https://dvc.org/doc/user-guide/project-structure/internal-files)
  for ideas.
  GRR manage command could use this internal state to optimize decision for indexing
  given resource and for calculating the resource statistics

* We can use `.dvc` files for large resource files to skip calculation
  of md5 sums.


### Interaction with caching

While caching a resource files the caching GRR calculates its md5sum
to validate the copy with the manifest md5sum value. If the calculated
md5sum does not match the manifest md5sum value the copy of the resource
file is removed and and exception is raised.

So we don't need the timestamp
to decide the validity of the copied resource files.

When a resource file is in the cached resource this means that its md5sum
is equal to the md5sum value in the resource manifest.

When accessing a cached resource, the first step of the caching GRR is to get
the remote resource manifest and compare it to the cached manifest. If remote
manifest and cached manifest are different, the cached resource files that 
are different are removed from the cached resource, the remote manifest is
stored in the cached GRR and after that the cached resource is used. See
[Resource Caching](#resource-caching)

**We do not need timestamps for implementation of caching.**



