import allure
from test_helpers.helpers import execute_query_and_log


@allure.story('Data_Tables_Creation')
@allure.severity(allure.severity_level.CRITICAL)
@allure.description("""
Verifies that all device models from the agg_data table have corresponding entries in the device_segments table.
Uses the UPPER() function to ignore case sensitivity.
""")
def test_device_models_match(setup):
    """
    Verifies that all device models from the agg_data table have corresponding entries in the device_segments table.
    Uses the UPPER() function to ignore case sensitivity.
    """
    bq_client, env = setup
    agg_data = env.get_full_table_id('agg_data')
    device_segments = env.get_full_table_id('device_segments')

    query = f"""
        -- Select distinct device models from the agg_data table after converting them to uppercase
        SELECT DISTINCT UPPER(agg.device_model) AS device_model_upper
        -- Specify the agg_data table from which the data will be selected, using the alias 'agg'
        FROM `{agg_data}` agg
        -- Select device models that do not exist in the device_segments table
        WHERE UPPER(agg.device_model) NOT IN (
          -- Subquery to select distinct device models from the device_segments table after converting them to uppercase
          SELECT DISTINCT UPPER(ds.device_model)
          -- Specify the device_segments table from which data will be selected for the subquery, using the alias 'ds'
          FROM `{device_segments}` ds
        )
    """

    # Use our helper function to execute the query and log it in Allure.
    results = execute_query_and_log(bq_client, query,
                                    "Checking device model matches",
                                    include_query_in_message=False)

    # Convert the results into a list for further processing.
    missing_models = [row.device_model_upper for row in results]

    # If there are devices in agg_data that are missing in device_segments, output an error message.
    assert len(missing_models) == 0, f"Found devices in agg_data that are missing in device_segments::\n" + "\n".join(
        missing_models)


@allure.story('Data_Tables_Creation')
@allure.severity(allure.severity_level.NORMAL)
@allure.description("""
Tests the presence of corresponding entries in the device_segments table for each record in the agg_data table, 
ensuring data integrity between apps and devices.
""")
def test_missing_device_data(setup):
    """
    Verifies the presence of corresponding entries in the device_segments table for each record in the agg_data table.
    """
    bq_client, env = setup
    agg_data = env.get_full_table_id('agg_data')
    app_names = env.get_full_table_id('app_names')
    device_segments = env.get_full_table_id('device_segments')

    query = f"""
        -- Select data about apps and device models
        SELECT agg.app_id, agg.device_model, an.app_name, an.platform
        -- From the agg_data table using the alias 'agg'
        FROM `{agg_data}` agg
        -- Join the app_names table using the alias 'an' by app_id
        JOIN `{app_names}` an ON agg.app_id = an.app_id
        -- Left join with the device_segments table using the alias 'ds' by device model, case insensitive
        LEFT JOIN `{device_segments}` ds ON UPPER(agg.device_model) = UPPER(ds.device_model)
            -- Also check for matching app name and platform between app_names and device_segments
            AND an.app_name = ds.app_short AND an.platform = ds.platform
        -- Condition to select records that do not have a corresponding device model in device_segments
        WHERE ds.device_model IS NULL
    """

    results = execute_query_and_log(bq_client, query, "Finding unmatched data in device_segments",
                                    include_query_in_message=False)

    failed_items = [(row.app_id, row.device_model, row.app_name, row.platform) for row in results]

    with allure.step("Verifying the absence of records without matching device models in device_segments"):
        assert not failed_items, "Found records in agg_data without matching device models in device_segments:\n" + \
                                 "\n".join(
                                     f"App ID: {app_id}, Device Model: {device_model}, App Name: {app_name}, Platform: {platform}"
                                     for app_id, device_model, app_name, platform in failed_items)


@allure.story('Data_Tables_Creation')
@allure.severity(allure.severity_level.NORMAL)
@allure.description("""
Verifies the uniqueness of records in the device_segments table based on the combination of device_model and segment, 
ensuring no duplicates, which is critical for data integrity.
""")
def test_device_segments_uniqueness(setup):
    """
    Verifies the uniqueness of records in the device_segments table based on the combination of device_model and segment.
    """
    bq_client, env = setup
    device_segments = env.get_full_table_id('device_segments')

    query = f"""
        -- Find duplicates based on the combination of device_model and segment
        -- This helps ensure that each device model and segment is uniquely identified in the table
        SELECT device_model, segment, COUNT(*) as cnt
        FROM `{device_segments}`
        GROUP BY device_model, segment
        -- Filter groups with more than one record, indicating the presence of duplicates
        HAVING cnt > 1
    """

    results = execute_query_and_log(bq_client, query, "Finding duplicates in device_segments",
                                    include_query_in_message=False)

    duplicates = [(row.device_model, row.segment, row.cnt) for row in results]

    with allure.step("Verifying the absence of duplicates in device_segments"):
        assert not duplicates, "Found duplicates in device_segments:\n" + \
                               "\n".join(
                                   f"Device Model: {device_model}, Segment: {segment}, Count: {cnt}"
                                   for device_model, segment, cnt in duplicates)


@allure.story('Data_Tables_Creation')
@allure.severity(allure.severity_level.CRITICAL)
@allure.description("""
Ensures that there are no records in the agg_data table with an installation date earlier than January 1, 2020, 
ensuring the data's relevance and correctness.
""")
def test_agg_data_date_range(setup):
    """
    Verifies that there are no records in the agg_data table with an installation date earlier than January 1, 2020.
    """
    bq_client, env = setup
    agg_data = env.get_full_table_id('agg_data')

    # Form a query to ensure that there are no records with an installation date earlier than '2020-01-01'
    query = f"""
        -- Find records in agg_data with an installation date earlier than '2020-01-01'
        SELECT COUNT(*) as cnt
        FROM `{agg_data}`
        WHERE install_date < '2020-01-01'
    """

    # Use our helper function to execute the query and log it in Allure
    results = execute_query_and_log(bq_client, query, "Checking the installation date range",
                                    include_query_in_message=False)

    # Get the count of records that fall outside the specified date range and process the query result
    count_out_of_range = next(results).cnt

    # Ensure there are no installations before '2020-01-01'
    with allure.step("Verifying the absence of installations before '2020-01-01'"):
        assert count_out_of_range == 0, f"Found installations before '2020-01-01' {count_out_of_range}"


@allure.story('Data_Tables_Creation')
@allure.severity(allure.severity_level.NORMAL)
@allure.description("""
Ensures that all values in the installs column of the agg_data table are positive, thereby guaranteeing that the 
application installation data is valid and logical.
""")
def test_agg_data_positive_installs(setup):
    """
    Verifies that all install values in the agg_data table are positive.
    """
    bq_client, env = setup
    agg_data = env.get_full_table_id('agg_data')

    query = f"""
        -- Find records in agg_data with non-positive installs (installs <= 0)
        SELECT COUNT(*) as cnt
        FROM `{agg_data}`
        WHERE installs <= 0
    """

    # Execute the query and log it in Allure
    results = execute_query_and_log(bq_client, query, "Finding non-positive install values",
                                    include_query_in_message=False)

    # Extract the count of records with non-positive install values
    count_non_positive = next(results).cnt

    with allure.step("Verifying the absence of non-positive install values in agg_data"):
        assert count_non_positive == 0, f"Found non-positive install values: {count_non_positive}"


@allure.story('Data_Tables_Creation')
@allure.severity(allure.severity_level.CRITICAL)
@allure.description("""
Verifies that every app_id from the agg_data table has a corresponding entry in the app_names table, ensuring data 
consistency between tables.
""")
def test_app_names_consistency(setup):
    """
    Verifies app_id consistency between the agg_data and app_names tables.
    This test ensures that all app_id values used in agg_data are correctly defined and present in app_names.
    """
    bq_client, env = setup
    agg_data = env.get_full_table_id('agg_data')
    app_names = env.get_full_table_id('app_names')

    query = f"""
        -- Performs a LEFT JOIN between the agg_data and app_names tables using the app_id column.
        -- This allows us to verify each app_id from agg_data to ensure there is a corresponding record in app_names.
        -- If a corresponding record in app_names is not found (i.e., the result of the JOIN is NULL for this row),
        -- such app_ids are considered "missing" in app_names.
        SELECT ad.app_id
        FROM `{agg_data}` ad
        LEFT JOIN `{app_names}` an ON ad.app_id = an.app_id
        WHERE an.app_id IS NULL  -- Only selects app_ids that do not have a match in app_names.
    """

    # Execute the query and log it in Allure
    missing_app_ids = execute_query_and_log(bq_client, query,
                                            "Verifying app_id consistency between agg_data and app_names",
                                            include_query_in_message=False)

    # Convert the results into a list of app_ids for easier assertion
    missing_app_ids_list = [row.app_id for row in missing_app_ids]

    with allure.step("Verifying the absence of app_ids from agg_data without corresponding records in app_names"):
        assert not missing_app_ids_list, f"Found app_ids from agg_data missing in app_names: {', '.join(missing_app_ids_list)}"


@allure.story('Data_Tables_Creation')
@allure.severity(allure.severity_level.NORMAL)
@allure.description("""
Verifies the app_names table to ensure there are no duplicate app_ids where the same app_id is associated with different 
app_name or platform. 
""")
def test_app_names_no_duplicate_ids(setup):
    """
    Verifies the absence of duplicate app_ids associated with different app_name or platform in the app_names table.
    """
    bq_client, env = setup
    app_names = env.get_full_table_id('app_names')

    # Form an SQL query to find duplicate app_ids associated with different app_name or platform.
    query = f"""
        SELECT app_id, COUNT(DISTINCT app_name) as unique_app_names, COUNT(DISTINCT platform) as unique_platforms
        FROM `{app_names}`
        GROUP BY app_id
        -- Group records by app_id to aggregate data. This allows us to count the number of
        -- unique app_name and platform values associated with each app_id.
        -- The HAVING condition is applied after grouping to filter out groups where
        -- the number of unique app_name or platform values exceeds 1. This indicates duplicates:
        -- cases where a single app_id is associated with multiple names or platforms.
        HAVING unique_app_names > 1 OR unique_platforms > 1
    """

    # Use the helper function to execute the query and log it in Allure
    duplicates = execute_query_and_log(bq_client, query,
                                       "Finding duplicates for app_id with different app_name or platform",
                                       include_query_in_message=False)

    # Convert the query results into a list for easier subsequent verification
    # Each element of the list contains app_id and the count of unique app_name and platform values for that app_id.
    duplicate_details = [(row.app_id, row.unique_app_names, row.unique_platforms) for row in duplicates]

    with allure.step("Verifying the absence of duplicate app_ids with different app_name or platform"):
        assert not duplicate_details, f"Found app_ids with multiple app_names or platforms: {duplicate_details}"


@allure.story('Data_Tables_Creation')
@allure.severity(allure.severity_level.CRITICAL)
@allure.description("""
Verifies the consistency between app names and platforms in the app_names and device_segments tables. 
This ensures that each app and its corresponding platform are correctly reflected in both tables, 
maintaining data integrity.
""")
def test_app_names_platform_consistency(setup):
    """
    Verifies that each app name and corresponding platform from the app_names table
    has a match in the device_segments table.
    """
    bq_client, env = setup
    app_names = env.get_full_table_id('app_names')
    device_segments = env.get_full_table_id('device_segments')

    # Query to verify consistency of app names and platforms between app_names and device_segments tables.
    query = f"""
        -- Query to verify consistency of app names and platforms between app_names and device_segments tables.
        -- Uses LEFT JOIN to link records from app_names with corresponding records in device_segments.
        -- The condition ON an.app_name = ds.app_short AND an.platform = ds.platform ensures matching on both key fields.
        -- The condition WHERE ds.app_short IS NULL OR ds.platform IS NULL filters cases where corresponding records in device_segments are missing,
        -- indicating inconsistency between the tables.  
        SELECT an.app_name, an.platform
        FROM `{app_names}` an
        LEFT JOIN `{device_segments}` ds ON an.app_name = ds.app_short AND an.platform = ds.platform
        WHERE ds.app_short IS NULL OR ds.platform IS NULL
    """

    # Use our helper function to execute the query and log it in Allure.
    inconsistencies = execute_query_and_log(bq_client, query,
                                            "Verifying consistency of app names and platforms",
                                            include_query_in_message=False)

    # Convert the query results into a list for easier verification.
    inconsistencies_details = [(row.app_name, row.platform) for row in inconsistencies]

    with allure.step("Verifying the absence of inconsistent app names and platforms"):
        assert not inconsistencies_details, "Verifying the absence of inconsistent app names and platforms " + \
                                            ", ".join(f"app_name: {app_name}, platform: {platform}" for app_name, platform in
                                                      inconsistencies_details)
