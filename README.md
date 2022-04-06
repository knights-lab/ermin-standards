# Emissions Report Minimum INformation (ERMIN) Standards
<p align="center">
  <img src="https://github.com/knights-lab/ermin-standards/blob/main/images/ermin-square-logo.jpg?raw=true" width="300" height="300">
</p>

## Background
This repository contains template files describing recommended minimum information, or metadata fields, that should be provided with any emissions report from any sector or using any observation method, as well as suggested optional metadata fields that may be included from only certain sectors or observation types. The templates also give a specification of the data format for the different metadata fields. The repository also includes software for validation of data tables.

## Templates
The primary XLSX-formatted specification can be found [here](https://github.com/knights-lab/ermin-standards/blob/main/templates/ermin-specification.xlsx?raw=true). 

## Usage
Run with:
```bash
python validate_ermin_table.py -s ermin-specification.csv -i testinput1.csv -o t1-fix.csv -v -a
```
