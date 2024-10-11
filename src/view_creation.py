import os
from google.cloud import bigquery
from google.oauth2 import service_account
from dotenv import load_dotenv

# Load environment variables from a file located at the project root
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Initialize environment variables
service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
project_id = os.getenv("GCP_PROJECT_ID")
dataset_id = os.getenv("BIGQUERY_DATASET_ID")

# Create a BigQuery client
credentials = service_account.Credentials.from_service_account_file(service_account_path)
client = bigquery.Client(credentials=credentials, project=project_id)

# SQL code for creating a view with explicit full table names
view_query = f"""
CREATE OR REPLACE VIEW `{project_id}.{dataset_id}.v_agg_data` AS
WITH agg AS (
    SELECT
        app_id,
        install_date,
        device_model,
        installs
    FROM `{project_id}.{dataset_id}.agg_data`
    WHERE install_date >= '2020-02-01'
),

dev_seg AS (
    SELECT
        segment,
        app_short,
        platform,
        UPPER(device_model) AS device_model
    FROM `{project_id}.{dataset_id}.device_segments`
    WHERE ua_team = 'network'
)

SELECT
    agg.install_date,
    agg.device_model,
    `{project_id}.{dataset_id}.app_names`.app_name,
    COALESCE(ds.segment, 'non_target_device') AS device_segment,
    agg.installs
FROM agg
INNER JOIN `{project_id}.{dataset_id}.app_names` ON agg.app_id = `{project_id}.{dataset_id}.app_names`.app_id
LEFT JOIN
    dev_seg AS ds ON
    agg.device_model IS NOT NULL AND `{project_id}.{dataset_id}.app_names`.platform = ds.platform
    AND `{project_id}.{dataset_id}.app_names`.app_name = ds.app_short AND ds.device_model = agg.device_model
LEFT JOIN
    `{project_id}.{dataset_id}.geo_segments`
    ON `{project_id}.{dataset_id}.app_names`.platform = `{project_id}.{dataset_id}.geo_segments`.platform AND `{project_id}.{dataset_id}.geo_segments`.ua_team = 'Network';
"""

# Execute the query to create the view
try:
    client.query(view_query).result()  # Attempt to execute the query to create the view
    print("View v_agg_data has been created successfully.")
except Exception as e:
    print(f"Failed to create view v_agg_data: {e}")
