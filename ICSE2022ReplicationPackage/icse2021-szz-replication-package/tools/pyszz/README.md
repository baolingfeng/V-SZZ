# PySZZ
This is an open-source implementation of several versions of the SZZ algorithm for detecting bug-inducing commits.

## Requirements
To run PySZZ you need:

- Python 3
- srcML (https://www.srcml.org/) (i.e., the `srcml` command should be in the path)
- git >= 2.23

## Setup
Run the following command to install the required python dependencies:
```
pip3 install --no-cache-dir -r requirements.txt
```

## Run
To run the tool, simply execute the following command:

```
python3 main.py /path/to/bug-fixes.json /path/to/configuration-file.yml /path/to/cloned-repo-directory
```
where:

- `bug-fixes.json` contains a list of information about bug-fixing commits and (optionally) issues
- `configuration-file.yml` is one of the following, depending on the SZZ variant you want to run:
    - `conf/agszz.yaml`: runs AG-ZZ
    - `conf/lszz.yaml`: runs L-ZZ
    - `conf/rszz.yaml`: runs R-ZZ
    - `conf/maszz.yaml`: runs MA-ZZ
    - `conf/raszz.yaml`: runs RA-ZZ
    - `conf/pdszz.yaml`: runs PyDriller-SZZ
- `cloned-repo-directory` is a folder which contains all the repositories that are required by `bug-fixes.json`

To have different run configurations, just create or edit the configuration files. The available parameters are described in each yml file.

