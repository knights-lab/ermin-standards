import ermin.syntax as es


def test_check_syntax():
    """Ensure check_syntax behaves as expected

       There are several known types, but these are mostly tested 
       in tests of smaller functions.
    """
    # test {text}
    syntax = "{text}"
    value = 'abc123'
    warnings, errors = es.check_syntax(value,syntax)
    assert len(warnings) == 0
    assert len(errors) == 0

    # test for error on missing value
    syntax = "{text}"
    value = ''
    warnings, errors = es.check_syntax(value,syntax,error_on_missing_value=True)
    assert len(warnings) == 0
    assert len(errors) == 1
    assert errors[0] == "Required field is empty."

    # test for no error on missing value when suppressed
    syntax = "{text}"
    value = ''
    warnings, errors = es.check_syntax(value,syntax)
    assert len(warnings) == 0
    assert len(errors) == 0

    syntax = '{unfccc_cat}'
    value = '3.D Agricultural Soils'
    warnings, errors = es.check_syntax(value, syntax)
    assert len(warnings) == 0
    assert len(errors) == 0

    # test that unfccc_cat checks can ignore whitespace
    syntax = '{unfccc_cat}'
    value = '3.D    AgriculturalSoils'
    warnings, errors = es.check_syntax(value, syntax)
    assert len(warnings) == 0
    assert len(errors) == 0

    # test invalid unfccc category
    syntax = '{unfccc_cat}'
    value = '3.D Cultural Soils'
    warnings, errors = es.check_syntax(value, syntax)
    assert len(warnings) == 0
    assert len(errors) == 1
    assert errors[0] == 'Invalid UNFCCC category: "' + value + '".'

    syntax = '{wkt}'
    value = 'POINT (50.586825 6.408977)'
    warnings, errors = es.check_syntax(value, syntax)
    assert len(warnings) == 1
    assert len(errors) == 0
    assert warnings[0] == "Syntax is {wkt}, but no automatic checking available yet. Value is: " + value
    
    syntax = '[A|B]'
    value = 'A'
    warnings, errors = es.check_syntax(value, syntax)
    assert len(warnings) == 0
    assert len(errors) == 0

    syntax = '[A|B]'
    value = 'C'
    warnings, errors = es.check_syntax(value, syntax)
    assert len(warnings) == 0
    assert len(errors) == 1
    assert errors[0] == 'Invalid value: "' + value + '". Accepted syntax: [A|B].'

def test_get_string_type_match_errors_timestamps():
    """Ensure get_string_type_match_errors catches possible errors in timestamp format
    """
    # test valid timestamps
    valid_timestamps = ['2008','2008-09','2008-09-12','2008-09-12T00','2008-09-12T23:59','2008-09-12T23:59:01','2008-09-12T23:59:01+02:33']
    for value in valid_timestamps:
        res = es.get_string_type_match_errors(value,'{timestamp}')
        assert len(res) == 0

    # test invalid timestamps
    invalid_timestamps = ['08',
                          '200a',
                          '88-09',
                          '2008-1-1',
                          '1/1/2008'
                          '1/1/08',
                          'Mar 3, 2020'
                          '2008-09-12T3:24',
                          '2008-09-12T23:59d',
                          '2008-09-12T23:59:01+02',
                          'NA']
    for value in invalid_timestamps:
        res = es.get_string_type_match_errors(value,'{timestamp}')
        expected = 'Invalid ISO format timestamp: "' + value + '". Format is "YYYY-[MM-[DD[*HH[:MM[:SS[.fff[fff]]]][+HH:MM[:SS[.ffffff]]]]]]".'
        assert len(res) is 1
        assert res[0] == expected

def test_get_string_type_match_errors_float():
    """Ensure get_string_type_match_errors catches possible errors in timestamp format
    """
    # test valid floats
    valid_floats = ['2008','.1','-12','-12.33333333','0.0','0']
    for value in valid_floats:
        res = es.get_string_type_match_errors(value,'{float}')
        assert len(res) == 0

    # test invalid timestamps
    invalid_floats = ['08d',
                      '1/2',
                      'NA',
                      '0.3.6']
    for value in invalid_floats:
        res = es.get_string_type_match_errors(value,'{float}')
        expected = 'Could not convert this value to a float: "' + value + '"'
        assert len(res) is 1
        assert res[0] == expected


def test_get_string_type_match_errors_doi():
    """Ensure get_string_type_match_errors catches possible errors in DOI
    """
    # test valid floats
    valid_doi = ['doi:10.1001/issn.103992','doi:10.1001.9939393/issn.103992','DOI:10.9d92j/issn.103.d.d.d.992','doi:10.9fjj0j02j/diojisdkj2--xx.___-e9lj']
    for value in valid_doi:
        res = es.get_string_type_match_errors(value,'{doi}')
        assert len(res) == 0

    # test invalid timestamps
    invalid_doi = ['doi:10.1001.10.3/issn.103992',
                   '10.1001.10/issn.103992',
                   'doi:10.9fjj0j0;];];/diojidlkw.d..w.d..w']
    for value in invalid_doi:
        res = es.get_string_type_match_errors(value,'{doi}')
        expected = 'Invalid DOI format: "' + value + '".'
        assert len(res) is 1
        assert res[0] == expected

def test_get_string_type_match_errors_url():
    """Ensure get_string_type_match_errors catches possible errors in URL
    """
    # test valid floats
    valid_url = ['http://www.google.com','https://www.google.com','http://abc.net']
    for value in valid_url:
        res = es.get_string_type_match_errors(value,'{url}')
        assert len(res) == 0

    # test invalid timestamps
    invalid_url = ['htp://www.google.com',
                   'http//www.google.com',
                   'http:/www.google.com',
                   'http://www.google.',                   
                   'abc.net']
    for value in invalid_url:
        res = es.get_string_type_match_errors(value,'{url}')
        expected = 'Invalid URL format: "' + value + '".'
        assert len(res) is 1
        assert res[0] == expected

def test_matches_syntax_list():
    """Ensure matches_syntax_list works as expected
    """

    # list with combination option
    syntax = "[RMSE|NRMSE|MAE|MAPE|SD|HIST|CI{float}|other]"
    # valid
    values = ["RMSE","NRMSE","MAE","MAPE","SD","HIST","CI.9","CI.95","CI0.95","CI9999","other"]
    for value in values:
        res = es.matches_syntax_list(value,syntax)
        assert res is True

    # list with combination option starting with {float}
    syntax = "[RMSE|{float}_version]"
    # valid
    res = es.matches_syntax_list('0.0001_version',syntax)
    assert res is True
    
    # invalid
    values = ["0.0001version", "RMS"]
    for value in values:
        res = es.matches_syntax_list(value,syntax)
        assert res is False

    # Another example
    syntax = "[20-year|100-year]"
    # valid
    res = es.matches_syntax_list('100-year',syntax)
    assert res is True

    # Single-character list
    syntax = "[1|2|3]"
    # valid
    res = es.matches_syntax_list('2',syntax)
    assert res is True

    # invalid
    res = es.matches_syntax_list('',syntax)
    assert res is False
    res = es.matches_syntax_list('22',syntax)
    assert res is False

    # Chemical formula list
    syntax = "[CO2|CH4|N2O|HFC-23_CHF3|HFC-134a_CH2FCF3|HFC-152a_CH3CHF2|CF4|C2F6|C3F8|C4F10|c-C4F8|C5F12|C6F14|SF6|NF3|SF5CF3|C4F9OC2H5|CHF2OCF2OC2F4OCHF2|CHF2OCF2OCHF2|CF3I|CH2Br2|CHCl3|CH3Cl|CH2Cl2|other]"
    # valid
    values = ["CO2","c-C4F8","other"]
    for value in values:
        res = es.matches_syntax_list(value,syntax)
        assert res is True

    # invalid
    values = ["CCC","-"]
    for value in values:
        res = es.matches_syntax_list(value,syntax)
        assert res is False



def test_get_string_type_match_errors_list():
    """Ensure get_string_type_match_errors catches possible errors in list format
    """
    # test {float} lists
    syntax = '{float},...'
    values = ['2008,-234.3,0.9, .111','2']
    for value in values:
        res = es.get_string_type_match_errors(value,syntax)
        assert len(res) == 0

    values = ['2008, abc','']
    for value in values:
        res = es.get_string_type_match_errors(value,syntax)
        assert len(res) == 1
        assert res[0] == 'One or more values in list do not match expected format ("{float}"): ' + value 

    # test {float} lists
    syntax = '{float}, ...'
    values = ['2008,-234.3,0.9, .111','2']
    for value in values:
        res = es.get_string_type_match_errors(value,syntax)
        assert len(res) == 0

    # test {text} lists
    syntax = '{text},...'
    values = ['2008,x-234.3,0.9, .111','hello world','']
    for value in values:
        res = es.get_string_type_match_errors(value,syntax)
        assert len(res) == 0


def test_get_string_type_match_errors_unknown_type():
    """Ensure get_string_type_match_errors catches possible errors in list format
    """
    # test {float} lists
    syntax = '{flot}' # invalid type
    value = '2008,-234.3,0.9, .111'
    try:
        res = es.get_string_type_match_errors(value,syntax)
    except ValueError as e:
        assert str(e) == 'Error: unknown stringtype "{flot}"'
