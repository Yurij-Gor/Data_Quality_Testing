import allure
from test_helpers.helpers import execute_query_and_log


@allure.severity(allure.severity_level.CRITICAL)
@allure.description("Testing that the application installation dates are within the expected range.")
@allure.story('View_Creation')
def test_date_range(setup):
    """
    Tests that application installation dates are within the expected range.
    """
    bq_client, env = setup  # Use the setup fixture to get the BigQuery client and configuration
    v_agg_data = env.get_full_table_id('v_agg_data')  # Retrieve the full ID of the v_agg_data table
    start_date = "2020-01-01"

    # Formulate the query to check the date range
    query = f"""
    -- Select records with installation dates outside the expected range
    -- The condition checks that the installation date is not earlier than '{start_date}' and not later than the current date
    SELECT COUNT(*) as cnt
    FROM `{v_agg_data}`
    WHERE install_date < '{start_date}' OR install_date > CURRENT_DATE()
    """

    # Use the helper function to execute the query and log it in Allure
    results = execute_query_and_log(bq_client, query, "Checking installation dates within the expected range",
                                    include_query_in_message=False)
    count_out_of_range = next(results).cnt  # Get the count of records outside the range

    # Check that there are no records with installation dates outside the specified range
    with allure.step(f"Verifying that there are no records with installation dates outside the range after {start_date} and before the current date"):
        assert count_out_of_range == 0, f"Found installations with dates outside the range after {start_date} and before the current date"


@allure.story('View_Creation')
@allure.severity(allure.severity_level.NORMAL)
@allure.description("""
Tests the data type consistency for the installs column in the v_agg_data view. 
Checks that all values are numeric and correctly cast to INT64.
""")
def test_data_type_consistency(setup):
    """
    Tests the data type consistency for the v_agg_data view.
    """
    bq_client, env = setup
    v_agg_data = env.get_full_table_id('v_agg_data')

    # Formulate the SQL query to check that all values in the installs column can be safely cast to INT64
    # and do not contain invalid data.
    query_installs = f"""
        -- Check data type consistency for the installs column in the v_agg_data view
        -- Select records where casting installs to INT64 returns NULL, indicating invalid data
        SELECT install_date, installs
        FROM `{v_agg_data}`
        WHERE SAFE_CAST(installs AS INT64) IS NULL
    """

    # Use the helper function to execute the query and log it in Allure.
    results = execute_query_and_log(bq_client, query_installs, "Checking data types for installs column",
                                    include_query_in_message=False)

    # Collect the list of records with potentially invalid values in installs.
    """ 
    We iterate through each row in the query result. For each row, we create a tuple containing the installation date 
    (install_date) and the number of installs (installs). To access the attribute 'installs', we use the function getattr(), 
    which allows us to safely retrieve the attribute value by its name (in this case, 'installs'). 
    If the attribute 'installs' is missing from the row (which shouldn't happen, but we check just in case), the function 
    will return None. Thus, failed_installs will contain a list of tuples, each corresponding to a row in the query result 
    where the number of installs couldn't be cast to INT64 
    (i.e., where the condition SAFE_CAST(installs AS INT64) IS NULL is true). This list contains records that potentially 
    have invalid data in the installs column.
    """
    failed_installs = [(row.install_date, getattr(row, 'installs', None)) for row in results]

    # Ensure the list is empty, indicating no invalid data types in installs.
    with allure.step("Verifying that there are no records with incorrect data types in installs"):
        assert len(failed_installs) == 0, f"Records with invalid installs values found: {failed_installs}"


@allure.severity(allure.severity_level.CRITICAL)
@allure.description("""
Tests for unrealistic high installation values in the v_agg_data view. 
Checks that for all applications, the total number of installs does not exceed the set threshold.
""")
@allure.story('View_Creation')
def test_unrealistic_high_installs(setup):
    """
    Tests for unrealistic high installation values.
    """
    bq_client, env = setup
    v_agg_data = env.get_full_table_id('v_agg_data')
    threshold = 1000000  # Threshold for identifying unrealistic high values

    # Formulate the query to count the total number of installs per application and filter those exceeding the threshold.
    query = f"""
        -- Count total installs per application
        SELECT app_name, SUM(installs) as total_installs
        FROM `{v_agg_data}`
        -- Group by application name
        GROUP BY app_name
        -- Filter applications where total installs exceed the set threshold
        HAVING total_installs > {threshold}
    """

    # Use the helper function to execute the query and log it in Allure.
    results = execute_query_and_log(bq_client, query,
                                    f"Checking for unrealistic high install values, threshold: {threshold}",
                                    include_query_in_message=False)

    # Convert the results to a list for further analysis
    excessive_installs = [(row.app_name, row.total_installs) for row in results]

    # Verify no applications exceed the install threshold
    with allure.step(f"Verifying that no applications exceed {threshold} installs"):
        assert len(excessive_installs) == 0, (f"Applications with unrealistic high install values found: "
                                              f"{excessive_installs}")


@allure.story('View_Creation')
@allure.severity(allure.severity_level.NORMAL)
@allure.description("""
Tests for application installs with undefined device models in the v_agg_data view.
""")
def test_undefined_device_model_installs(setup):
    """
    Tests for application installs with undefined device models.
    """
    bq_client, env = setup
    v_agg_data = env.get_full_table_id('v_agg_data')

    # Formulate the query to select app names and count installs where the device model is undefined or empty.
    query = f"""
        -- Select app names and count installs where the device model is undefined or an empty string
        SELECT app_name, COUNT(*) as total_installs
        FROM `{v_agg_data}`
        WHERE device_model IS NULL OR device_model = ''
        GROUP BY app_name
    """

    # Use the helper function to execute the query and log it in Allure.
    results = execute_query_and_log(bq_client, query, "Checking for installs with undefined device models",
                                    include_query_in_message=False)

    # Convert query results to a list of tuples for further analysis.
    undefined_device_model_installs = [(row.app_name, row.total_installs) for row in results]

    # If any installs with undefined device models are found, compile an error message with details.
    if len(undefined_device_model_installs) > 0:
        error_message = "Applications with undefined device model installs found:\n"
        for app_name, total_installs in undefined_device_model_installs:
            error_message += f"App Name: {app_name}, Install Count: {total_installs}\n"
        assert False, error_message
    else:
        assert True, "No installs found with undefined device models."


@allure.story('View_Creation')
@allure.severity(allure.severity_level.CRITICAL)
@allure.description("""
Verifies that each device segment from v_agg_data exists in device_segments or is marked as 'non_target_device'.
""")
def test_v_agg_data_segment_existence(setup):
    """
    Verifies that each device segment from v_agg_data exists in device_segments or is marked as 'non_target_device'.
    """
    bq_client, env = setup
    v_agg_data = env.get_full_table_id('v_agg_data')
    device_segments = env.get_full_table_id('device_segments')

    # Formulate the query to check the existence of each device segment from v_agg_data in device_segments,
    # excluding the 'non_target_device' segment. This query uses a subquery with EXISTS to check if the corresponding
    # segment exists in device_segments.
    query = f"""
        -- Select unique device segments from v_agg_data
        SELECT DISTINCT v.device_segment
        FROM `{v_agg_data}` v
        -- Filter segments other than 'non_target_device' and check their existence in device_segments
        WHERE v.device_segment <> 'non_target_device' AND NOT EXISTS (
            -- Subquery checks if the segment from v_agg_data exists in device_segments.
            -- 'SELECT 1' is used to verify the existence of the record: returns 1 if a record is found.
            SELECT 1
            FROM `{device_segments}` ds
            WHERE v.device_segment = ds.segment
        )
    """
    # Execute the query and log it in Allure using the execute_query_and_log function.
    results = execute_query_and_log(bq_client, query, "Verifying device segment existence",
                                    include_query_in_message=False)

    # Convert the query results to a list of missing device segments.
    missing_segments = [row.device_segment for row in results]

    # If missing segments are found, compile an error message.
    assert len(missing_segments) == 0, f"Missing device segments found in v_agg_data that are not present in device_segments: {missing_segments}"
