# inSPIRE-interactive

Easy GUI/webserver access for the inSPIRE platform.

<img src="https://raw.githubusercontent.com/QuantSysBio/inSPIRE/master/img/inSPIRE-logo.png" alt="drawing" width="200"/>


To start inSPIRE-Interaractive run:

inSPIRE-interactive

conda activate inspire-interact

inspire-interact --config_file config_mascot.yml

To see changes 
ctrl + C
inspire-interact --config_file config_mascot.yml

## Set Up

### Before Downloading

If you are working on Mac with an M1 chip you will require Miniforge. For all other users, any version of conda will suffice.


### Setting up your environment:


1) To start with create a new conda environment with python version 3.9:

```
conda create --name inspire python=3.11
```

2) Activate this environment

```
conda activate inspire
```

3) You will then need to install the inSPIRE-interactive package (this also installs inSPIRE):

```
pip install inspire-interact
```

4) To check your installation, run the following command (it is normal for this call to hang for a few seconds on first execution)

```
inspire-interact -h
```

5) You will require Percolator for rescoring. On Linux, Percolator can be installed via conda with the command below. Otherwise see https://github.com/percolator/percolator.

```
conda install -c bioconda percolator
```

Once you have successfully installed inSPIRE-Interactive you should run it specifying your pipeline and the mode of execution. The core execution of inSPIRE will take the form:

```
inspire-interact --config_file path-to-config-file --mode mode-of-execution
```

where the config file is a yaml file specifying configuration of your inSPIRE-Interactive server and the mode is either "server" if you are setting up inSPIRE-Interactive for use throughout your lab, or "local" if you are only using inSPIRE-Interactive on your own machine.
