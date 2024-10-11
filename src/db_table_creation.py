import os
import json
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

# Table schemas
schema_agg_data = [
    bigquery.SchemaField("app_id", "INTEGER"),
    bigquery.SchemaField("install_date", "DATE"),
    bigquery.SchemaField("device_model", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("installs", "INTEGER"),
]

schema_app_names = [
    bigquery.SchemaField("app_id", "INTEGER"),
    bigquery.SchemaField("app_name", "STRING"),
    bigquery.SchemaField("platform", "STRING"),
]

schema_device_segments = [
    bigquery.SchemaField("device_model", "STRING"),
    bigquery.SchemaField("segment", "STRING"),
    bigquery.SchemaField("app_short", "STRING"),
    bigquery.SchemaField("platform", "STRING"),
    bigquery.SchemaField("ua_team", "STRING"),
]

schema_geo_segments = [
    bigquery.SchemaField("geo", "STRING"),
    bigquery.SchemaField("segment", "STRING"),
    bigquery.SchemaField("platform", "STRING"),
    bigquery.SchemaField("ua_team", "STRING"),
]

# Function to load data from a JSON file into BigQuery with a specified schema
def load_json_to_bigquery(client, dataset_id, json_filepath, table_name, schema):
    table_id = f"{client.project}.{dataset_id}.{table_name}"
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    with open(json_filepath, 'rb') as file:
        job = client.load_table_from_json(json.load(file), table_id, job_config=job_config)
    job.result()  # Wait for the job to complete
    print(f"Data loaded into {table_id}")
    return table_id

# Function to update the .env file
def update_env_file(env_path, updates):
    with open(env_path, 'r') as file:
        lines = file.readlines()

    new_lines = []
    for line in lines:
        key = line.split('=')[0]
        if key in updates:
            new_line = f"{key}='{updates[key]}'\n"
        else:
            new_line = line
        new_lines.append(new_line)

    with open(env_path, 'w') as file:
        file.writelines(new_lines)


# Define paths and load data with explicit schema
base_path = os.path.join(os.path.dirname(__file__), '..', 'data')
json_files_schemas = {
    "agg_data.json": ("agg_data", schema_agg_data),
    "app_names.json": ("app_names", schema_app_names),
    "device_segments.json": ("device_segments", schema_device_segments),
    "geo_segments.json": ("geo_segments", schema_geo_segments),
}

env_updates = {}
for json_file, (table_name, schema) in json_files_schemas.items():
    json_filepath = os.path.join(base_path, json_file)
    full_table_id = load_json_to_bigquery(client, dataset_id, json_filepath, table_name, schema)
    env_var = f"BIGQUERY_TABLE_{table_name.upper()}_ID"
    env_updates[env_var] = full_table_id

update_env_file(dotenv_path, env_updates)
