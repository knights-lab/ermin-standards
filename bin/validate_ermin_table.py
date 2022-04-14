#!/usr/bin/env python3
# Dependencies
# pytest
import argparse
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
                        help='Print all warnings and errors to stdout (default print up to 10).')
    parser.add_argument('-v', '--verbose', help='More verbose output',
                        action='store_true')
    args = parser.parse_args()

    warnings, errors = check_input_file(args.input, args.specification, args.output)

    # Print warnings and errors:
    if(len(errors) > 0):
        if(args.all_errors):
            print('\n' + str(len(errors)) + ' errors were found. Printing all errors:')
            print("\n".join(errors))
        else:
            print(str(len(errors)) + ' errors were found. Printing up to 10:')
            print("\n".join(errors[:10]))


    if(len(warnings) > 0):
        if(args.all_errors):
            print('\n' + str(len(warnings)) + ' warnings were found. Printing all warnings:')
            print("\n".join(warnings))
        else:
            print(str(len(warnings)) + ' warnings were found. Printing up to 10:')
            print("\n".join(warnings[:10]))


