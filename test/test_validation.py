import ermin.validation as ev

def test_load_spec():
    """Ensure load_rules returns a list of dicts with
       at least these required fields in each row:
            Structured name, Required, Required by,
            Column number, Definition, Expected value,
            Value syntax, Example, Default, ERMIN ID
    """
    expected_headers = ["Structured name", "Required", "Required by",
            "Column number", "Definition", "Expected value",
            "Value syntax", "Example", "Default", "ERMIN ID"]

    rows = ev.load_spec('testdata/ermin-specification.csv')
    assert type(rows) is list

    for row in rows:
        assert type(row) is dict
        for expected_header in expected_headers:
            assert expected_header in row.keys()

def test_load_input():
    """Ensure load_input returns a header list and list of rows
       when run on a valid input file
       testdata1 includes these headers:
          original_inventory_sector  unfccc_annex_1_category unfccc_annex_1_category_notes   measurement_method_doi_or_url   producing_entity_name   producing_entity_id producing_entity_id_type    reporting_entity    emitted_product_formula emission_quantity   emission_quantity_units carbon_equivalency_method   start_time  end_time    data_version    data_version_changelog

    """
    expected_headers = ["original_inventory_sector", "unfccc_annex_1_category", "unfccc_annex_1_category_notes", "measurement_method_doi_or_url", "producing_entity_name", "producing_entity_id", "producing_entity_id_type", "reporting_entity", "emitted_product_formula", "emission_quantity", "emission_quantity_units", "carbon_equivalency_method", "start_time", "end_time", "data_version", "data_version_changelog"]

    header, rows = ev.load_input('testdata/testinput1.csv')
    assert type(header) is list
    assert type(rows) is list

    for expected_header in expected_headers:
        assert expected_header in header

    for row in rows:
        assert type(row) is list
        assert len(row) == len(header)

def test_check_input_header():
    """Ensure check_input_header detects missing required fields
    """
    # load spec
    spec = ev.load_spec('testdata/ermin-specification.csv')

    # testinput2 is missing column "data_version_changelog"
    header, rows = ev.load_input('testdata/testinput2.csv')
    warning_list, error_list = ev.check_input_header(header, spec)
    assert len(warning_list) == 0
    assert len(error_list) == 1

    expected = ['Missing this required column: "data_version_changelog".']
    for f in expected:
        assert f in error_list

    # testinput3 is missing columns "reporting_timestamp", "unfccc_annex_1_category", "data_version_changelog"  
    header, rows = ev.load_input('testdata/testinput3.csv')
    warning_list, error_list = ev.check_input_header(header, spec)
    assert len(warning_list) == 0
    assert len(error_list) == 3
    expected = ['Missing this required column: "unfccc_annex_1_category".', 'Missing this required column: "data_version_changelog".', 'Missing this required column: "reporting_timestamp".']
    for f in expected:
        assert f in error_list



def test_check_input_rows():
    """Ensure check_input_rows detects all errors
    """
    # load spec
    spec = ev.load_spec('testdata/ermin-specification.csv')

    print('\n')
    # testinput1 is valid
    header, rows = ev.load_input('testdata/testinput1.csv')
    warnings, errors = ev.check_input_rows(header, rows, spec)
    print('\n'.join(warnings[:5]))
    print('\n'.join(errors[:5]))

    print('\n')

    # testinput2 is missing column "data_version_changelog" but otherwise valid
    header, rows = ev.load_input('testdata/testinput2.csv')
    warnings, errors = ev.check_input_rows(header, rows, spec)
    print('\n'.join(warnings))
    print('\n'.join(errors))

    print('\n')

    # testinput3 is missing columns "unfccc_annex_1_category", "data_version_changelog", "reporting_timestamp"
    header, rows = ev.load_input('testdata/testinput3.csv')
    warnings, errors = ev.check_input_rows(header, rows, spec)
    print('\n'.join(warnings[:5]))
    print('\n'.join(errors[:5]))

def test_replace_missing_values():
    """Ensure replace_missing_values replaces missing values
    """

    header, rows = ev.load_input('testdata/testinput3-missing-values.csv')

    # try not in place
    newrows = ev.replace_missing_values(header, rows, ['emission_quantity'], replace_with='TEST',in_place=False)
    for i in range(18,24):
        assert newrows[i][8] == "TEST"

    # try in place
    ev.replace_missing_values(header, rows, ['emission_quantity'], replace_with='TEST',in_place=True)
    for i in range(18,24):
        assert rows[i][8] == "TEST"

    # try replacing all missing
    header, rows = ev.load_input('testdata/testinput3-missing-values.csv')
    ev.replace_missing_values(header, rows, column_names = None, replace_with='TEST',in_place=True)
    for i in range(len(rows)):
        assert rows[i][1] == "TEST"
    for i in range(18,24):
        assert rows[i][8] == "TEST"
    for i in range(len(rows)):
        assert rows[i][13] == "TEST"

def test_add_columns():
    """Ensure add_columns functions as expected
    """

    # testinput3 is missing columns "unfccc_annex_1_category", "data_version_changelog", "reporting_timestamp"
    header, rows = ev.load_input('testdata/testinput3-missing-values.csv')

    # add "unfccc_annex_1_category"
    n_columns_before = len(header)
    ev.add_columns(header, rows, ['unfccc_annex_1_category'], fill_with='TEST',in_place=True)

    # assert there is one additional column
    assert len(header) == n_columns_before + 1
    for i in range(len(rows)):
        assert len(rows[i]) == n_columns_before + 1
    # assert new column named 'unfccc_annex_1_category'
    assert header[-1] == 'unfccc_annex_1_category'

    # assert new column is filled with "TEST"
    for i in range(len(rows)):
        assert rows[i][-1] == "TEST"
