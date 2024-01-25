# inSPIRE-interactive

Easy GUI/webserver access for the inSPIRE platform.

<img src="https://raw.githubusercontent.com/QuantSysBio/inSPIRE/master/img/inSPIRE-logo.png" alt="drawing" width="200"/>


## Set Up

### Before Downloading

We recommend working with inSPIRE through conda. On windows systems you may also need

### Setting up your environment:

For basic inSPIRE-Interactive use.

1) To start with create a new conda environment with python version 3.11:

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

6) Once you have successfully installed inSPIRE-Interactive you should run it specifying your pipeline and the mode of execution. The core execution of inSPIRE will take the form:

```
inspire-interact --config_file path-to-config-file --mode local
```

where the config file is a yaml file specifying configuration of your inSPIRE-Interactive server and the mode is either "server" if you are setting up inSPIRE-Interactive for use throughout your lab, or "local" if you are only using inSPIRE-Interactive on your own machine.

7) On local mode you can then access the webserver home by pasting the following address on your browser:

```
http://127.0.0.1:5000/interact-page/home
```

## Additional Features

In order to use raw files on Linux or Mac O.S. you will require the use of mono ([mono project](https://www.mono-project.com/download/stable/)) which is required by the ThermoRawFileParser. (The ThermoRawFileParser itself is open source and downloaded by inSPIRE.)

In order to use NetMHCpan for binding affinity prediction you should download the software from the [DTU site](https://services.healthtech.dtu.dk/services/NetMHCpan-4.1/) (you must agree to the license agreement). On linux and maxos systems we typically use tcsh.

In order to use MSFragger within inSPIRE-Interactive you should download from [MSFragger](https://github.com/Nesvilab/MSFragger/wiki/Preparing-MSFragger#Downloading-MSFragger) (you must agree to the license agreements). You will also need java which can be installed using:

```
conda install -c conda-forge openjdk
```

In order to use Skyline within inSPIRE-Interactive you will need to download docker and insure can be run within inSPIRE. See instructions from [docker documentation](https://docs.docker.com/desktop/). (Skyline itself is open source).


## Writing the Config File.

The following configurations should be set for inSPIRE-interactive:

| Key   | Description   |
|-------|---------------|
| maxInspireCpus | The number of CPUs from your computer that you wish to dedicate to inSPIRE execution.  |
| fraggerPath    | The file path to the .jar file of MSFragger (e.g. for version 3.7 the end of this path should be: MSFragger-3.7/MSFragger-3.7.jar) |
| fraggerMemory  | The ammount of memory (GB) that is available for MSFragger execution. |
| netMHCpan      | The command that can be used to run NetMHCpan (e.g. on Linux we use [tcsh](https://www.cyberciti.biz/faq/howto-install-csh-shell-on-linux/) to execute NetMHCpan and so our config key is ```tcsh /data/inSPIRE-Server/netMHCpan-4.1/netMHCpan```). |


## Example of Windows Config


```
---
fraggerPath:  C:/Program Files/MSFragger-3.7/MSFragger-3.7.jar
fraggerMemory: 240
maxInspireCpus: 20
skylineRunner: C:/Program Files/Skyline/SkylineRunner.exe
rescoreCommand: C:/Program Files/percolator-v3-05/bin/percolator.exe
```
