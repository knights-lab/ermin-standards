import ermin.validation as ev
import pandas as pd

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

    # testinput1 is valid
    header, rows = ev.load_input('testdata/testinput1.csv')
    warnings, errors = ev.check_input_rows(header, rows, spec)

    # testinput2 is missing column "data_version_changelog" but otherwise valid
    header, rows = ev.load_input('testdata/testinput2.csv')
    warnings, errors = ev.check_input_rows(header, rows, spec)

    # testinput3 is missing columns "unfccc_annex_1_category", "data_version_changelog", "reporting_timestamp"
    header, rows = ev.load_input('testdata/testinput3.csv')
    warnings, errors = ev.check_input_rows(header, rows, spec)

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

def test_check_input_dataframe(tmp_path):
    """Ensure Pandas wrapper works
    """
    # Create test data frame
    df = pd.DataFrame(columns = ['original_inventory_sector','unfccc_annex_1_category_notes','measurement_method_doi_or_url','producing_entity_name','producing_entity_id','producing_entity_id_type','reporting_entity','emitted_product_formula','emission_quantity','emission_quantity_units','start_time','end_time','data_version'])

    # Add records to dataframe using the .loc function
    df.loc[0] = ['Agricultural Soils','','https://www.fao.org/faostat/en/','Afghanistan','AFG','iso3_country','Hudson Carbon','CO2','2752210.5','t','2015-01-01','2015-12-31','0.9']
    df.loc[1] = ['Agricultural Soils','','https://www.fao.org/faostat/en/','Afghanistan','AFG','iso3_country','Hudson Carbon','CO2','3033958.5','t','2016-01-01','2016-12-31','0.9']
    df.loc[2] = ['Agricultural Soils','','https://www.fao.org/faostat/en/','Afghanistan','AFG','iso3_country','Hudson Carbon','CO2','3168578.5','t','2017-01-01','2017-12-31','0.9']
    df.loc[3] = ['Agricultural Soils','','https://www.fao.org/faostat/en/','Afghanistan','AFG','iso3_country','Hudson Carbon','CO2','2775212.5','t','2018-01-01','2018-12-31','0.9']
    df.loc[4] = ['Agricultural Soils','','https://www.fao.org/faostat/en/','Afghanistan','AFG','iso3_country','Hudson Carbon','CO2','3011407','t','2019-01-01','2019-12-31','0.9']
    df.loc[5] = ['Agricultural Soils','','https://www.fao.org/faostat/en/','Afghanistan','AFG','iso3_country','Hudson Carbon','CO2','3011407','t','2020-01-01','2020-12-31','0.9'] 

    # Check functionality without repairing data
    warnings, errors = ev.check_input_dataframe(df, spec_file='testdata/ermin-specification.csv', repair=False)

    expected = ['Missing this required column: "unfccc_annex_1_category".', 'Missing this required column: "data_version_changelog".', 'Missing this required column: "reporting_timestamp".']
    assert len(warnings) == 0
    for error in errors:
        assert error in expected 
    assert len(errors) == len(expected)

    # Check functionality when repairing data
    warnings, errors, newdf = ev.check_input_dataframe(df, spec_file='testdata/ermin-specification.csv', repair=True)
    expected_warnings = 'Adding missing fields: unfccc_annex_1_category, data_version_changelog, reporting_timestamp.', 'Replacing missing values with NULL in all columns.'
    expected_errors = ['Missing this required column: "unfccc_annex_1_category".', 'Missing this required column: "data_version_changelog".', 'Missing this required column: "reporting_timestamp".']
    for warning in warnings:
        assert warning in expected_warnings 
    assert len(warnings) == len(expected_warnings)
    for error in errors:
        assert error in expected_errors
    assert len(errors) == len(expected_errors)


    # Check functionality when repairing data, not writing file
    warnings, errors, newdf = ev.check_input_dataframe(df, spec_file='testdata/ermin-specification.csv', repair=True)

    expected_warnings = ['Adding missing fields: unfccc_annex_1_category, data_version_changelog, reporting_timestamp.', 'Replacing missing values with NULL in all columns.']
    expected_errors = ['Missing this required column: "unfccc_annex_1_category".', 'Missing this required column: "data_version_changelog".', 'Missing this required column: "reporting_timestamp".']
    for warning in warnings:
        assert warning in expected_warnings 
    assert len(warnings) == len(expected_warnings)
    for error in errors:
        assert error in expected_errors
    assert len(errors) == len(expected_errors)


    # Check functionality when repairing data  and writing file
    output_file = tmp_path / 'tmp.csv'
    warnings, errors, newdf = ev.check_input_dataframe(df, spec_file='testdata/ermin-specification.csv', repair=True, output_file=str(output_file))

    expected_warnings = ['Writing repaired file to ' + str(output_file) + '.', 'Adding missing fields: unfccc_annex_1_category, data_version_changelog, reporting_timestamp.', 'Replacing missing values with NULL in all columns.']
    expected_errors = ['Missing this required column: "unfccc_annex_1_category".', 'Missing this required column: "data_version_changelog".', 'Missing this required column: "reporting_timestamp".']
    for warning in warnings:
        assert warning in expected_warnings 
    assert len(warnings) == len(expected_warnings)
    for error in errors:
        assert error in expected_errors
    assert len(errors) == len(expected_errors)

    # load file, check header for new values, check rows for NULL where missing values were
    expected_header = ['original_inventory_sector','unfccc_annex_1_category_notes','measurement_method_doi_or_url','producing_entity_name','producing_entity_id','producing_entity_id_type','reporting_entity','emitted_product_formula','emission_quantity','emission_quantity_units','start_time','end_time','data_version',
                        'unfccc_annex_1_category', 'data_version_changelog', 'reporting_timestamp']
    header, rows = ev.load_input(output_file)
    for i in range(len(rows)):
        assert rows[i][1] == "NULL"
