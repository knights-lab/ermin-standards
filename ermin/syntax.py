# functions for checking field syntax
from datetime import datetime
import validators
import re
import inspect
from ermin import unfccc_utils

def check_syntax(value,syntax,error_on_missing_value = False):
    """Check that value matches syntax

       Known syntax possibilities are:
       {text}
       {unfccc_cat},...
       {float}
       {timestamp}
       [{float}|NULL]
       [{doi}|{url}]
       {wkt}
       [20-year|100-year]
       [1|2|3]
       [CO2|CH4|N2O|HFC-23_CHF3|HFC-134a_CH2FCF3|HFC-152a_CH3CHF2|CF4|C2F6|C3F8|C4F10|c-C4F8|C5F12|C6F14|SF6|NF3|SF5CF3|C4F9OC2H5|CHF2OCF2OC2F4OCHF2|CHF2OCF2OCHF2|CF3I|CH2Br2|CHCl3|CH3Cl|CH2Cl2|other]
       [RMSE|NRMSE|MAE|MAPE|SD|HIST|CI{float}|other]
       [carbon_dioxide|methane|nitrous oxide|hydroflurocarbons|perfluorocarbons|sulphur_hexafluoride|nitrogen_trifluoride|trifluoromethyl_sulphur_pentafluoride|halogenated_ethers|other halocarbons|other_halogenated_ghgs|other]
       [TRUE|FALSE]
    """
    error_list = []
    warning_list = []

    # remove multiple/trailing spaces
    value = re.sub(r'\s+',' ',value).strip()
    syntax = re.sub(r'\s+',' ',syntax).strip()

    # remove spaces after commas in syntax and value
    value = value.replace(', ',',')
    syntax = syntax.replace(', ',',')

    # Could implement this is a very flexible and recursive way,
    # but there are few enough possibilities that it will be 
    # easier to read and write this code if we simply 
    # enumerate them explicitly
    if value == "" and error_on_missing_value:
        error_list.append("Required field is empty.")
    elif syntax == "{wkt}":
        warning_list.append("Syntax is {wkt}, but no automatic checking available yet. Value is: " + value)
    elif syntax.startswith("["):
        if not matches_syntax_list(value, syntax):
            error_list.append('Invalid value: "' + value + '". Accepted syntax: ' + syntax + '.')
    elif syntax.startswith("{"):
        errors = get_string_type_match_errors(value, syntax)
        if len(errors) > 0:
            error_list += errors

    return warning_list, error_list

def matches_syntax_list(value, syntax):
    """Check whether value matches syntax list

       Each item in list is either a string requiring exact match, 
       or a string type, or a combination (e.g. CI{float}).

       Accepted string types are {text}, {float}, {doi}, {url}, {timestamp}
       
       Nested lists not currently implemented.

       Only combinations of exact text match and {float} are
       supported, and the syntax must start or end with {float}, 
       e.g. CI{float} or {float}_version.
    
       Parameters:
       value (str): input value to be checked
       syntax (str): acceptable syntax description

       Returns:
       bool: True if syntax matches
    """
    is_match = False

    # split list into options
    options = syntax[1:-1].split('|')
    options = [option.strip() for option in options]
    # check each option for a match:
    for option in options:
        if option.startswith('{') and option.endswith('}'):
            # option is a string type
            error_list = get_string_type_match_errors(value, option)
            if len(error_list) == 0:
                is_match = True
        elif option.startswith('{float}'):
            # Get substring of option that needs to match exactly
            # e.g. CI
            exact_match_substring = option[7:]
            if value.endswith(exact_match_substring):
                # Get the part of value that is leftover after exact match
                float_substring = value[:-len(exact_match_substring)]
                errors = get_string_type_match_errors(float_substring,'{float}')
                if len(errors) == 0:
                    is_match = True
        elif option.endswith('{float}'):
            # Get substring of option that needs to match exactly
            # e.g. CI
            exact_match_substring = option[:-7]
            if value.startswith(exact_match_substring):
                # Get the part of value that is leftover after exact match
                float_substring = value[len(exact_match_substring):]
                errors = get_string_type_match_errors(float_substring,'{float}')
                if len(errors) == 0:
                    is_match = True
        else:
            # option is an exact string match 
            if value.strip() == option:
                is_match = True
    return is_match

def get_string_type_match_errors(value, stringtype):
    """Checks whether value matches stringtype.

       Accepted string types are {text}, {float}, {doi}, {url}, {timestamp},
       or comma-delimed list versions of these, e.g. {text},... or {float},...

       Parameters:
       value (str): input value to be checked
       stringtype (str): acceptable syntax description

       Returns:
       list: list of errors, empty if no errors
    """
    error_list = []

    if stringtype == "{float}":
        # check if we can cast this as a float, unless it's an allowed NULL
        try:
            float(value)
        except ValueError:
            error_list.append('Could not convert this value to a float: "' + value + '"')
    elif stringtype == "{timestamp}":
        if not is_valid_timestamp(value):
            error_list.append('Invalid ISO format timestamp: "' + value + '". Format is "YYYY-[MM-[DD[*HH[:MM[:SS[.fff[fff]]]][+HH:MM[:SS[.ffffff]]]]]]".')
    elif stringtype == "{unfccc_cat}":
        if not unfccc_utils.is_valid_unfccc_cat(value, ignore_all_whitespace=True):
            error_list.append('Invalid UNFCCC category: "' + value + '".')
    elif stringtype == "{doi}":
        # DOI format e.g. 10.1038/issn.1476-4687 or 10.1038.388/issn.1476-4687 
        # Does not support non-alphanumeric registrant codes
        # (e.g. "-","_", extra "." not allowed)
        match_result = re.match(r'^doi:10\.[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)?/[a-zA-Z0-9.\-_]+$',value.lower().strip())
        if match_result is None:
            error_list.append('Invalid DOI format: "' + value + '".')
    elif stringtype == "{url}":
        # Check for valid http:// URL
        is_valid = True
        if not value.lower().startswith('http://') and not value.lower().startswith('https://'):
            is_valid = False
        else:
            if not validators.url(value):
                is_valid = False
        if not is_valid:
            error_list.append('Invalid URL format: "' + value + '".')
    elif stringtype.endswith(', ...') or stringtype.endswith(',...'):
        # call recursively on first element in list (e.g. {float} for {float, ...})
        stringtype_substring = stringtype[:stringtype.find(',')]
        valid = True
        # split value by commas
        values = [v.strip() for v in value.split(',')]

        for v in values:
            # Checking each value in list against basic stringtype
            error_list_v = get_string_type_match_errors(v,stringtype_substring)
            if len(error_list_v) > 0:
                valid = False
        if not valid:
            error_list.append('One or more values in list do not match expected format ("' + stringtype_substring + '"): ' + value) 
    elif stringtype != '{text}':
        raise ValueError('Error: unknown stringtype "' + stringtype + '"')

    return error_list

def is_valid_timestamp(timestamp):
    """Checks whether timestamp string is a proper ISO 8601 timestamp

       Format is YYYY-MM-DD[*HH[:MM[:SS[.fff[fff]]]][+HH:MM[:SS[.ffffff]]]]
       e.g. 2008-01-23T19:23:10+00:00

       Parameters:
       timestamp (str): timestamp string to be checked

       Returns:
       bool: True if proper timestamp string

    """

    # if YYYY, add fake month to work with built-in ISO test
    if re.match(r"^\d{4}$", timestamp) is not None:  
        timestamp += "-01"

    # if YYYY-MM, add fake day to work with built-in ISO test
    if re.match(r"^\d{4}-\d{2}$", timestamp) is not None:
        timestamp += "-01"
    
    # Check ISO format using built-in test    
    try:
        datetime.fromisoformat(timestamp)
    except ValueError:
        return False
    return True

