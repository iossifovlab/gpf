# Setup Project Environment

## Download Anaconda

The GPF project uses Anaconda python distribution for *Python 2.7*. You need
to download Anaconda installer from *Continuum Analytics* 
[web site](https://www.continuum.io/downloads):

```
wget -c https://repo.continuum.io/archive/Anaconda2-4.4.0-Linux-x86_64.sh
```

After downloading the *Anaconda* installer you need to run the installer

```
bash Anaconda2-4.4.0-Linux-x86_64.sh
```

and follow the installer instructions.

## Install the GPF environment

To install the GPF environment you need to use the environment description
file `root-anaconde-environment.yml` located into the root directory of the
project:

```
conda env update -f root-anaconda-environment.yml
```

## Prepare environment setup script

