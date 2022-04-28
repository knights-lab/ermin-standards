# Emissions Report Minimum INformation (ERMIN) Standards

## Background
This repository contains template files describing recommended minimum information, or metadata fields, that should be provided with any emissions report from any sector or using any observation method, as well as suggested optional metadata fields that may be included from only certain sectors or observation types. The templates also give a specification of the data format for the different metadata fields.

The repository also includes software for validation and correction of data tables.

## Templates
The primary XLSX-formatted specification can be found [here](https://github.com/knights-lab/ermin-standards/blob/main/templates/ermin-specification.xlsx?raw=true). 

## Installation
- Download this repo ([zipped version](https://github.com/knights-lab/ermin-standards/archive/refs/heads/main.zip) or, better, clone with `git`)
- Permanently add the full path to its top-level directory to the [system environment variable](https://stackoverflow.com/questions/3402168/permanently-add-a-directory-to-pythonpath) `PYTHONPATH`. After reopening your terminal, you should now be able to run `import ermin` from a Python interpreter anywhere on your system.
- Optionally, permanently add the full path to the `bin` directory to the [system environment variable](https://stackoverflow.com/questions/14637979/how-to-permanently-set-path-on-linux-unix) `PATH`. This will allow you to run ERMIN executables from anywhere on your system (i.e. just run `validate_ermin_table.py`). Otherwise, run with `python /path/to/repo/bin/validate_ermin_table.py`.

## Requirements:
- `python` version >= 3.6
- `validators` package
- `pandas` package
- `pytest` package for running unit tests
- Mac or Linux (may work on Windows, but not tested).

## Usage

### To use as a module:
Validate a Pandas dataframe:
```python
import ermin.validation as ev
import pandas as pd

# load CSV into a Pandas DataFrame
# Notes: use comment='#' to skip comment lines
#        use keep_default_na=False to ensure that empty fields remain strings
#        optionally, use dtype = str to keep all fields as strings
df = pd.read_csv('test/testdata/testinput3.csv', comment='#', keep_default_na=False)

# Example 1: Validate DataFrame using provided spec file, returning a new repaired DataFrame
warnings, errors, newdf = ev.check_input_dataframe(df,spec_file='templates/ermin-specification.csv')

# Example 2: Validate DataFrame using provided spec file, saving repaired table to file
warnings, errors, newdf = ev.check_input_dataframe(df,spec_file='templates/ermin-specification.csv', output_file='t1-fix.csv')
```

Validate a CSV file and save repaired table to a new file:
```python
import ermin.validation as ev

# Validate file and write a repaired version to new file
warnings, errors = check_input_file('test/testdata/testinput1.csv, 'templats/ermin-specification.csv', output_file='t1-fix.csv')
```

### To use from the command line:
Print instructions with:
```bash
python validate_ermin_table.py -h
```

Check test file, replace all missing values with NULL:
```bash
python validate_ermin_table.py -s ermin-specification.csv -i test/testdata/testinput1.csv -o t1-fix.csv -v -a
```

Check two test files, replace all missing values with NULL:
```bash
python bin/validate_ermin_table.py -s templates/ermin-specification.csv -i test/testdata/testinput1.csv -o t1-fix.csv -v -a
python bin/validate_ermin_table.py -s templates/ermin-specification.csv -i test/testdata/testinput2.csv -o t2-fix.csv -v -a
```

## Testing
Run unit tests from within the `test` folder. Requires `pytest` package.
```bash
pytest
```
