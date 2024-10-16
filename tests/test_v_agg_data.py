import allure
from test_helpers.helpers import execute_query_and_log


# Test to verify that there are no app installations before January 1, 2020
@allure.severity(allure.severity_level.CRITICAL)
@allure.description("Testing that there are no app installations before January 1, 2020.")
@allure.story('View_Creation')
def test_install_date_post_2020(setup):
    """Testing that there are no app installations before January 1, 2020."""
    bq_client, env = setup  # Unpacking the values returned by the fixture
    v_agg_data = env.get_full_table_id('v_agg_data')  # Get the full ID of the v_agg_data table
    query = f"""
        -- Calculate the number of records where the app installation date is before January 1, 2020
        SELECT COUNT(*) as cnt
        -- From the v_agg_data table,
        FROM `{v_agg_data}`
        -- Condition to filter records by installation date
        WHERE install_date < '2020-01-01'
    """

    # Use the helper function to execute the SQL query and log it in Allure
    results = execute_query_and_log(bq_client, query, "Check for no installations before January 1, 2020", include_query_in_message=False)
    for row in results:
        with allure.step(f"Check that the number of installations = 0, actual: {row.cnt}"):
            assert row.cnt == 0, "Should be 0 installations before 2020-01-01"  # Test condition check


# Test to verify that there are no installations with zero or negative amounts
@allure.severity(allure.severity_level.CRITICAL)
@allure.description("Testing that there are no installations with zero or negative amounts.")
@allure.story('View_Creation')
def test_positive_installs(setup):
    """Testing that there are no installations with zero or negative amounts."""
    bq_client, env = setup  # Unpacking the values returned by the fixture
    v_agg_data = env.get_full_table_id('v_agg_data')  # Get the full ID of the v_agg_data table
    query = f"""
        -- Count the number of records where the number of installations is less than or equal to zero
        SELECT COUNT(*) as cnt
        -- Access the v_agg_data table
        FROM `{v_agg_data}`
        -- Condition to filter records by the number of installations
        WHERE installs <= 0
    """

    # Use the helper function to execute the SQL query and log it in Allure
    results = execute_query_and_log(bq_client, query,
                                    "Check for no installations with zero or negative amounts",
                                    include_query_in_message=False)
    for row in results:
        with allure.step(f"Check that the number of installations > 0, actual: {row.cnt}"):
            assert row.cnt == 0, "Should be 0 installations with non-positive numbers" # Test condition check


# Test to verify that there are no records with non-target device segments
@allure.story('View_Creation')
@allure.severity(allure.severity_level.NORMAL)
@allure.description("""
Tests the absence of records with non-target device segments in the v_agg_data view. 
Non-target segments are those that are either unspecified or explicitly marked as 'non_target_device'.
""")
def test_non_target_device_segments_absent(setup):
    bq_client, env = setup  # Unpacking the values returned by the fixture
    v_agg_data = env.get_full_table_id('v_agg_data')  # Get the full ID of the v_agg_data table
    detailed_query = f"""
        -- Select the device model and device segment from the v_agg_data view
        SELECT device_model, device_segment
        FROM `{v_agg_data}`
        -- Condition to filter records where the device segment is either unspecified (NULL)
        -- or explicitly marked as 'non_target_device'. This helps identify
        -- non-target device segments that may require additional data correction actions.
        WHERE device_segment IS NULL OR device_segment = 'non_target_device'
    """

    # Use the helper function to execute the SQL query and log it in Allure
    detailed_results = execute_query_and_log(bq_client, detailed_query,
                                             "Check for the absence of non-target device segments",
                                             include_query_in_message=False)

    detailed_failures = []
    with allure.step("Collecting non-target device segments"):
        for row in detailed_results:
            if row.device_segment is None or row.device_segment == 'non_target_device':
                detailed_failures.append((row.device_model, row.device_segment or 'NULL'))

    with allure.step("Verify that no non-target device segments are found"):
        assert len(
            detailed_failures) == 0, f"Expected 0 non-target device segments, found: {len(detailed_failures)}\n" + \
                                     "\n".join(f"Device Model: {model}, Segment: {segment}" for model, segment in
                                               detailed_failures)


@allure.story('View_Creation')
@allure.severity(allure.severity_level.NORMAL)
@allure.description("""
Verifies the absence of duplicates in the v_agg_data view. Duplicates may indicate issues in the data collection or processing process.
""")
def test_no_duplicates_in_view(setup):
    """
     Verifies the absence of duplicates in the v_agg_data view.
    """
    bq_client, env = setup  # Unpacking the values returned by the fixture
    v_agg_data = env.get_full_table_id('v_agg_data')  # Get the full ID of the v_agg_data table

    # Form the SQL query to check for duplicates in the data
    query = f"""
        SELECT app_name, device_model, install_date, installs, device_segment, COUNT(*) as cnt
        FROM `{v_agg_data}`  -- From the v_agg_data view
        GROUP BY app_name, device_model, install_date, installs, device_segment  -- Group by key fields
        HAVING cnt > 1  -- Condition to select groups with more than one record (duplicates)
    """

    # Use the helper function to execute the SQL query and log it in Allure
    results = execute_query_and_log(bq_client, query,
                                    "Checking for duplicates in the v_agg_data view",
                                    include_query_in_message=False)

    # Collect duplicate records for easier display in the error message
    duplicate_records = []
    with allure.step("Collecting information about found duplicates"):
        for row in results:
            duplicate_records.append(
                (row.app_name, row.device_model, row.install_date, row.installs, row.device_segment, row.cnt))

    # Check that the list of duplicates is empty; otherwise, report the issue
    with allure.step("Verify that there are no duplicates"):
        assert len(duplicate_records) == 0, "Duplicates found in the view:\n" + "\n".join(
            f"App: {record[0]}, Device Model: {record[1]}, Install Date: {record[2]}, Installs: {record[3]}, Device Segment: {record[4]}, Count: {record[5]}"
            for record in duplicate_records
        )


@allure.story('View_Creation')
@allure.severity(allure.severity_level.CRITICAL)
@allure.description("""
Verifies that the device segments specified in the v_agg_data view match those present in the device_segments table.
""")
def test_v_agg_data_proper_segment_use(setup):
    """
    Verifies the consistency of device segments between v_agg_data and device_segments.
    This test ensures that each device segment specified in the v_agg_data view
    exists in the device_segments table, except for the 'non_target_device' segment,
    which is an acceptable default value.
    """

    # Initialize BigQuery client and retrieve table identifiers
    bq_client, env = setup
    v_agg_data = env.get_full_table_id('v_agg_data')
    device_segments = env.get_full_table_id('device_segments')

    # SQL query to check that each device segment in v_agg_data exists in the device_segments table
    query = f"""
    SELECT 
      v.device_model, 
      v.device_segment,
      CASE 
        WHEN d.device_model IS NULL THEN 'Missing'  -- If there's no match in the device_segments table, set status to 'Missing'
        ELSE 'Present'  -- If there's a match, set status to 'Present'
      END AS segment_status
    FROM (
      SELECT DISTINCT device_model, device_segment
      FROM `{v_agg_data}`  -- Select unique pairs of device model and segment from v_agg_data
      WHERE device_segment != 'non_target_device'  -- Exclude the 'non_target_device' segment as it doesn't need validation
    ) AS v
    LEFT JOIN `{device_segments}` AS d  -- Join the device_segments table
    ON v.device_model = d.device_model AND v.device_segment = d.segment  -- Join condition: matching model and segment
    """

    # Execute the query and log it in Allure
    segment_checks = execute_query_and_log(bq_client, query, "Verifying device segment consistency",
                                           include_query_in_message=False)

    # Collect and verify results
    missing_segments = [(row.device_model, row.device_segment) for row in segment_checks if row.segment_status == 'Missing']

    # Assert no missing segments
    with allure.step("Verify the absence of missing device segments"):
        assert not missing_segments, f"Missing device segments found in device_segments: {missing_segments}"


@allure.story('View_Creation')
@allure.severity(allure.severity_level.CRITICAL)
@allure.description("""
Verifies that 'non_target_device' is used in the v_agg_data view only when there are no device segments available in the device_segments table.
""")
def test_non_target_device_usage(setup):
    """
    Verifies the correct use of 'non_target_device' in v_agg_data.
    This test ensures that 'non_target_device' is only used when there are no matching segments in device_segments.
    If device models exist in device_segments, using 'non_target_device' is considered incorrect.
    """
    bq_client, env = setup  # Unpack the fixture's return values
    v_agg_data = env.get_full_table_id('v_agg_data')  # Get the full ID of the v_agg_data table
    device_segments = env.get_full_table_id('device_segments')  # Get the full identifier of the device_segments table

    # Form the query to select device models with 'non_target_device' and check their presence in device_segments.
    query = f"""
    -- Select device models marked as 'non_target_device' and check their presence in the device_segments table.
    -- If the model exists in device_segments, it indicates incorrect use of the 'non_target_device' label.
    SELECT 
      v.device_model, 
      STRING_AGG(d.segment) AS expected_segments  -- Aggregate all segments associated with the device model into a string.
    FROM (
      SELECT DISTINCT device_model  -- Select unique device models labeled as 'non_target_device' from v_agg_data.
      FROM `{v_agg_data}`
      WHERE device_segment = 'non_target_device'
    ) v
    LEFT JOIN `{device_segments}` d ON v.device_model = d.device_model  -- Join with device_segments to check model existence.
    GROUP BY v.device_model
    HAVING COUNT(d.segment) > 0  -- Select only cases where the model has at least one segment in device_segments.
    """

    # Execute the query and log it in Allure
    results = execute_query_and_log(bq_client, query,
                                    "Checking incorrect use of 'non_target_device 'non_target_device'",
                                    include_query_in_message=False)

    # Collect information about models and segments for the error message.
    incorrect_models = []
    for row in results:
        incorrect_models.append(f"Model: '{row.device_model}', Expected segments: [{row.expected_segments}]")

    # Assert that no device models are incorrectly marked as 'non_target_device'.
    assert not incorrect_models, "Incorrect use of 'non_target_device' found:\n" + "\n".join(incorrect_models)
