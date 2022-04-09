#!/usr/bin/env python3
# Dependencies
# pytest
import argparse
from pathlib import Path
from ermin.validation import *

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-s','--specification', metavar='filename', type=str, 
                        help='CSV file giving ERMIN specification.')
    parser.add_argument('-i','--input', metavar='filename', type=str, 
                        help='Input file.')
    parser.add_argument('-o','--output', metavar='filename', type=str, default=None,
                        help='Output file with missing values filled and missing columns added (default None).')
    parser.add_argument('-a','--all_errors', action='store_true',
                        help='Print all errors to stdout (default None).')
    parser.add_argument('-v', '--verbose', help='More verbose output',
                        action='store_true')
    args = parser.parse_args()

    spec_rows = load_spec(args.specification)
    input_header, input_rows = load_input(args.input)
    warnings, errors = check_input(input_header, input_rows, spec_rows)

    if(len(warnings) > 0):
        if(args.all_warnings):
            print(str(len(warnings)) + ' warnings were found. Printing all warnings:')
            print("\n".join(warnings))
        else:
            print(str(len(warnings)) + ' warnings were found. Printing up to 10:')
            print("\n".join(warnings[:10]))

    if(len(errors) > 0):
        if(args.all_errors):
            print(str(len(errors)) + ' errors were found. Printing all errors:')
            print("\n".join(errors))
        else:
            print(str(len(errors)) + ' errors were found. Printing up to 10:')
            print("\n".join(errors[:10]))

    if args.output is not None:
        # replace missing columns
        missing_fields = get_missing_header_list(input_header, spec_rows)
        if(len(missing_fields) > 0):
            print('Adding missing fields: '+ ','.join(missing_fields) + '...')
            add_columns(input_header, input_rows, missing_fields)

        # replace missing values
        print('Replacing missing values with NULL in all columns...')
        replace_missing_values(input_header, input_rows, column_names=None)

        # write new output file
        path = Path(args.output)
        print(path.parent.absolute())
        path.parent.mkdir(parents=True, exist_ok=True)
        print('Writing repaired file to ' + args.output + '...')
        write_output(args.output, input_header, input_rows)


