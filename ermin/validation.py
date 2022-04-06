import csv
from ermin import syntax as es
from ermin import unfccc_utils

# load iterable filter (rather than old list-based filter)
# To avoid loading filtered file into memory
# from https://stackoverflow.com/questions/33715579/python-3-module-itertools-has-no-attribute-ifilter
try:
    # Python 2
    from future_builtins import filter
except ImportError:
    # Python 3
    pass

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


def check_input(input_header, input_rows, spec_rows, ):
    """Check one row of an input file against spec


       Parameters:

       Returns:
       new_header: a new repaired header for input file
       new_rows: new input file rows with repaired values

    """
    warnings, errors = check_input_header(input_header, spec_rows)
    warnings, errors = check_input_rows(input_header, input_rows, spec_rows)
    return warnings + warnings, errors + errors

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

