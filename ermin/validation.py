import csv
from ermin import syntax as es
from ermin import unfccc_utils
from pathlib import Path
import pandas as pd

# load iterable filter (rather than old list-based filter)
# To avoid loading filtered file into memory
# from https://stackoverflow.com/questions/33715579/python-3-module-itertools-has-no-attribute-ifilter
try:
    # Python 2
    from future_builtins import filter
except ImportError:
    # Python 3
    pass

# Wrapper function for using pandas DataFrame as input
def check_input_dataframe(input_df, spec_file=None, spec_rows=None, repair=True, output_file=None):
    """Check entire input data frame against spec file
       
       Either spec_file or spec_dict must be provided.
       
       Optionally repairs missing data according to specification.

       Parameters:
       input_df (DataFrame): Emissions report DataFrame
       spec_file (str): Path to specification CSV file or None.
       spec_dict (str): list of dicts of spec values keyed by spec headers or None.
       repair (bool): If True, repair missing/invalid and return new DataFrame
       output_file: If not None and repair, write repaired data to output file.

       Returns:
       warnings (list): a list of warnings encountered
       errors (list): a list of errors encountered
       newdf (DataFrame): only returned if repair

    """
    # Ensure that we have a valid specification
    if spec_file is not None:
        spec_rows = load_spec(spec_file)
    elif spec_rows is None:
        raise ValueError('check_input_dataframe requires either spec_file or spec_dict.')

    # Store original input dtypes
    
    # convert input DataFrame to header, rows
    input_header = list(input_df.columns)
    input_rows = input_df.values.tolist()

    warnings1, errors1 = check_input_header(input_header, spec_rows)
    warnings2, errors2 = check_input_rows(input_header, input_rows, spec_rows)
    warnings = warnings1 + warnings2
    errors = errors1 + errors2

    # repair data if requested
    if repair:
        new_warnings = repair_data(input_header, input_rows, spec_rows, output_file)
        warnings += new_warnings

        # Make new DF from header, rows, which have been repaired in place
        new_df = pd.DataFrame(data = input_rows,
                              columns = input_header,
                              index=input_df.index.tolist())
    elif output_file is not None:
        # if output file provided but not repair, raise an error
        raise ValueError('output_file provided but repair was False.')

    if repair:
        return warnings, errors, new_df
    else:
        return warnings, errors



def check_input_file(input_file, spec_file, output_file=None):
    """Check entire input file against spec file,
       Optionally output a new repaired file.

       If repaired output file is requested, input is edited in place and written out

       Parameters:
       input_file (str): Path to input data table CSV file
       spec_file (str): Path to specification CSV
       new_file (str): Path to new output file or None

       Returns:
       warnings (list): list of warning messages
       errors (list): list of error messages

    """

    # Load data
    spec_rows = load_spec(spec_file)

    # Load data
    input_header, input_rows = load_input(input_file)

    # Run the validation
    warnings, errors = check_input(input_header, input_rows, spec_rows)


    # Write a new output file with missing columns and filled values
    if output_file is not None:
        new_warnings = repair_data(input_header, input_rows, spec_rows, output_file)
        warnings += new_warnings

    return warnings, errors


def repair_data(input_header, input_rows, spec_rows, output_file=None):
    """Replaces values in input header, input rows _in place_

       If repaired output file is requested, input is edited in place and written out

       Parameters:
       input_header (list): List of column headers from input file
       input_rows (list): List of lists of fields from each input row
       spec_rows (list): List of header-keyed dicts of specification rows
       output_file (str): Path to output file for new data (or None)

       Returns:
       warnings (list): list of warning messages
    """

    warnings = []

    # replace missing columns
    missing_fields = get_missing_header_list(input_header, spec_rows)
    if(len(missing_fields) > 0):
        warnings.append('Adding missing fields: '+ ', '.join(missing_fields) + '.')
        add_columns(input_header, input_rows, missing_fields)

    # replace missing values
    warnings.append('Replacing missing values with NULL in all columns.')
    replace_missing_values(input_header, input_rows, column_names=None)

    if output_file is not None:
        # write new output file
        path = Path(output_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        warnings.append('Writing repaired file to ' + output_file + '.')
        write_output(output_file, input_header, input_rows)

    return warnings



# load rules from specification CSV
def load_spec(csv_filepath):
    """Load rules from CSV spec

    Parameters:
    csv_filepath -- full path to CSV file containing the ERMIN spec
                    Should contain at least these headers:
                      Structured name, Required, Required by,
                      Column number, Definition, Expected value,
                      Value syntax, Example, Default, ERMIN ID
    """
    # Get headers
    with open(csv_filepath, newline='', mode='r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = []
        try:
            for row in reader:
                if(len(row['Structured name'])) > 0:
                    # Skip empty rows
                    rows.append(row)
        except csv.Error as e:
            sys.exit('file {}, line {}: {}'.format(filename, reader.line_num, e))
    return rows

def load_input(csv_filepath):
    """Load input data from CSV

    Parameters:
    csv_filepath -- full path to CSV file containing the input file
    """
    # Get headers
    with open(csv_filepath, newline='', mode='r', encoding='utf-8-sig') as csvfile:
        # use filter to skip lines starting with '#'
        # use itertools to avoid loading whole file into memory
        # See https://stackoverflow.com/questions/14158868/python-skip-comment-lines-marked-with-in-csv-dictreader
        reader = csv.reader(filter(lambda row: row[0]!='#', csvfile))
        header = next(reader, None)
        rows = []
        try:
            for row in reader:
                if(len(row[0])) > 0:
                    # Skip empty rows
                    rows.append(row)
        except csv.Error as e:
            sys.exit('file {}, line {}: {}'.format(filename, reader.line_num, e))
    return header, rows

def write_output(csv_filepath, headers, rows):
    """Load rules from CSV spec

    Parameters:
    csv_filepath (str): full path to CSV file containing the input file
    """

    # Get headers
    with open(csv_filepath, newline='', mode='w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
 
def check_input_header(input_header, spec_rows):
    """Check input file header for compliance

       Specifically, are all required columns included?
       For those columns that are dependent on others, are they included?

       Returns: 
       error_list, a list of errors encountered
    """
    warning_list = []
    error_list = []
    missing_headers = get_missing_header_list(input_header, spec_rows)
    for missing_header in missing_headers:
        error_list.append('Missing this required column: "' + missing_header + '".')
    return warning_list, error_list

def get_missing_header_list(input_header, spec_rows):
    """Get list of required headers that are missing

       Returns: 
       field_list (list): list of names of missing required headers
    """
    field_list = []

    # check each spec variable if required
    for row in spec_rows:
        field_name = row['Structured name']
        is_required = row['Required']
        if is_required == "Yes":
            if field_name not in input_header:
                field_list.append(field_name)
    return field_list


def check_input(input_header, input_rows, spec_rows):
    """Check entire input data set (in list form) against spec

       Parameters:
       input_header (list): list of strings containing column headers
       input_rows (list): list of lists containing row values
       spec_rows (list): list of dicts of spec values keyed by spec headers

       Returns:
       warnings (list): a list of warnings encountered
       errors (list): a list of errors encountered

    """
    warnings1, errors1 = check_input_header(input_header, spec_rows)
    warnings2, errors2 = check_input_rows(input_header, input_rows, spec_rows)
    return warnings1 + warnings2, errors1 + errors2

def check_input_rows(input_header, input_rows, spec_rows):
    """Check input file rows for compliance

       Specifically, are any values missing in required columns?
       Do all entrys match required syntax?

       Parameters:
       input_header (list): List of column headers from input file
       input_rows (list): List of lists of fields from each input row
       spec_rows (list): List of header-keyed dicts of specification rows

       Returns:
       warnings (list): a list of warnings encountered
       errors (list): a list of errors encountered
    """
    error_list = []
    warning_list = []

    # check for values that don't match syntax or are required but missing
    for i in range(len(input_rows)):
        # for each row in input
        irow = input_rows[i]
        for srow in spec_rows:
            # for each column in spec, check if required and present,
            # and check if present and syntax matches
            field_name = srow['Structured name']
            is_required = srow['Required'] == "Yes"
            syntax = srow['Value syntax']
            if field_name in input_header:
                j = input_header.index(field_name)
                value = irow[j]
                warnings, errors = es.check_syntax(value, syntax, error_on_missing_value = is_required)
                for error in errors:
                    error = 'Error in row ' + str(i) + ', column ' + str(j) + ', field "' + field_name + '": ' + error
                    error_list.append(error)
                for warning in warnings:
                    warning = 'Warning in row ' + str(i) + ', column ' + str(j) + ', field "' + field_name + '": ' + warning
                    warning_list.append(warning)
    return warning_list, error_list

def replace_missing_values(input_header, input_rows, column_names,
                           replace_with="NULL", in_place=True):
    """Replace missing values in the requested columns

       Parameters:
       input_header (list): List of column headers from input file
       input_rows (list): List of lists of fields from each input row
       column_names (list): List of names of columns in which to replace
                            or None to replace in all columns
       replace_with (str): String with which to replace missing values
       in_place (bool): If True, will replace values _in place_

       Returns:
       new_rows (list): List of lists of fields from each input row, or None if in_place
    """

    if column_names is None:
        # replace in all columns
        column_names = input_header

    if not type(column_names) is list:
        raise ValueError('column_names paramter must be a list')

    if not in_place:
        # make a new copy of input rows
        newrows = [row.copy() for row in input_rows]

    # check for values that don't match syntax or are required but missing
    for i in range(len(input_rows)):
        # for each row in input
        for field_name in column_names:
            # for each column in which we are supposed to replace
            if field_name not in input_header:
                raise ValueError('Error: column name "' + field_name +'" not in input headers: ' + str(input_header))
            j = input_header.index(field_name)
            if input_rows[i][j] == "":
                if in_place:
                    input_rows[i][j] = replace_with
                else:
                    newrows[i][j] = replace_with

    if not in_place:
        return newrows


def add_columns(input_header, input_rows, column_names,
                           fill_with="NULL", in_place=True):
    """Add new columns filled with the requested value

       Parameters:
       input_header (list): List of column headers from input file
       input_rows (list): List of lists of fields from each input row
       column_names (list): List of names of columns to add
       fill_with (str): String with which to fill new columns
       in_place (bool): If True, will add values _in place_

       Returns:
       new_header (list): List of column headers, or None if in_place
       new_rows (list): List of lists of fields from each input row, or None if in_place
    """
    if not type(column_names) is list:
        raise ValueError('column_names paramter must be a list')

    if not in_place:
        # make a new copy of input rows and header
        newheader = input_header.copy()
        newrows = [row.copy() for row in input_rows]

    for column_name in column_names:
        if column_name in input_header:
            raise ValueError('Column name "' + column_name + '" already in input header.')
        if in_place:
            input_header.append(column_name)
        else:
            newheader.append(column_name)
        for i in range(len(input_rows)):
            if in_place:
                input_rows[i].append(fill_with)
            else:
                newrows[i].append(fill_with)

    if not in_place:
        return newheader, newrows


