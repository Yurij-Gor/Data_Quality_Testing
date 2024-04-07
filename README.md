# Data Quality Testing & CI/CD Demo Project

## Description
This project demonstrates data quality testing using Python and Pytest, coupled with a CI/CD pipeline employing Docker, Docker Compose, and GitHub Actions. It focuses on verifying data integrity within a Google BigQuery database. Test results are visualized using Allure and published on GitHub Pages.

## Test Results
View the Allure Test Report:  
[Allure Report](https://yurij-gor.github.io/Data_Quality_Testing/)

## Technologies
- **Python 3.x**: Core language for test scripting.
- **Pytest**: A framework for executing the tests.
- **Google BigQuery on Google Cloud Platform**: Cloud database with tables and views for testing.
- **Allure**: For test reporting.
- **Docker & Docker Compose**: Containerization and orchestration.
- **GitHub Actions**: Workflow automation for CI/CD.

## Installation
```bash
git clone https://github.com/Yurij-Gor/Data_Quality_Testing
cd Data_Quality_Testing
pip install -r requirements.txt
```

## BigQuery Setup

Included in this project are scripts for setting up tables and views within Google BigQuery. If you're looking to apply these scripts to your own BigQuery database, ensure you have your BigQuery environment properly configured beforehand. The scripts are designed to be easily adaptable for different BigQuery datasets, so you can leverage them for your data quality testing needs.

### Requirements for BigQuery

Before running the scripts, make sure you have:

- A Google Cloud Platform account with BigQuery enabled.
- The appropriate permissions and roles assigned to your account to create and manage BigQuery resources.
- A dataset created in BigQuery where the tables and views can be set up.

After confirming the above prerequisites, you can utilize the `db_table_creation.py` and `view_creation.py` scripts to construct your database schema and views within BigQuery.

### Environment Configuration

Create a `.env` file for local or CI/CD execution and a `docker.env` for Docker execution at the root of the project with your Google Cloud credentials and project information, as detailed in the previous sections.

```plaintext
# .env file for local or CI/CD execution
GOOGLE_APPLICATION_CREDENTIALS="path/to/your/google-credentials.json"
GCS_BUCKET_NAME="your_bucket_name"
GCP_PROJECT_ID="your_project_id"
BIGQUERY_DATASET_ID="your_dataset_id"
```

For Docker execution, create a docker.env file with similar contents:

```plaintext
# docker.env file for Docker execution
GOOGLE_APPLICATION_CREDENTIALS="/keys/your-google-credentials.json"
GCS_BUCKET_NAME="your_bucket_name"
GCP_PROJECT_ID="your_project_id"
BIGQUERY_DATASET_ID="your_dataset_id"
```

### Running the Scripts

To set up your BigQuery tables and views:

1. Make sure your `.env` or `docker.env` files are correctly set up with the necessary credentials.
2. Run the `db_table_creation.py` script to create and populate the tables in your BigQuery dataset.
3. Execute the `view_creation.py` script to establish the required views.

This process is part of an automated data pipeline that validates and tests your data, ensuring that the BigQuery tables and views are properly set up for quality assessment.

The scripts and testing framework provided here are designed to be adaptable for different BigQuery datasets, offering flexibility for your data quality testing needs. Ensure to replace the placeholders with your actual project data and file paths where necessary.

## About the Tests

The tests, located in the `tests/` directory, are necessary for maintaining the quality and integrity of the data. Data located in the Google BigQuery database. Tests are designed to validate various facets of the data, focusing on ensuring the reliability and correctness of the data. Below is an outline of the key testing areas covered:

- **Installations Data Validity**: These tests are pivotal in verifying that there are no records of installations prior to a specified date and that all reported installation figures are positive integers. This is fundamental in maintaining the integrity of the installations data.

- **Data Consistency**: Consistency checks are performed to ensure uniformity across device model segments in different tables. It's vital that every application ID found in one table corresponds accurately to entries in other related tables, thereby ensuring data coherence.

- **Duplication and Anomaly Detection**: Aimed at identifying any duplicate records or anomalies within the data, such as implausibly high numbers of installations or entries with undefined device models. These tests are essential for detecting and rectifying data inaccuracies.

- **Comprehensive Data Checks**: Beyond specific validations, these tests perform a broad spectrum of checks. They ascertain the presence of expected records, the absence of inappropriate or unexpected records, and the overall data integrity within the BigQuery dataset.

Each test is annotated with detailed descriptions and categorized according to severity levels, which aids in prioritizing the resolution of any issues detected. Integrated within the CI/CD pipeline, these automated tests play an indispensable role in continuously monitoring and upholding a high standard of data quality.


## Running Tests

To run the tests with detailed output and generate an Allure report, use the following command:

```bash
python -m pytest -vv --alluredir=<PathToTestResults> tests/
```

To generate and open the Allure report in a web browser:

```bash
allure serve <PathToTestResults>
```

### Running Tests with Docker
Before running the tests inside a Docker container, make sure Docker is installed on your system. Use these commands to control the Docker environment:
```bash
# Stop and remove containers, networks, images, and volumes
docker-compose down

# Build and start the project using docker-compose
docker-compose up --build
```

To copy the Allure report from the Docker container to your local machine and open it:

```bash
# Replace <ContainerName> with your actual running container's name
# and <LocalPathToStoreResults> with the local path where you want to store the test results
docker cp <ContainerName>:/tests_project/test_results <LocalPathToStoreResults>

# To serve the Allure report, navigate to the directory where the results are stored and run:
allure serve <LocalPathToStoreResults>/test_results
```
Remember to clean up after your Docker environment once you're done:
```bash
docker-compose down
```
Ensure to replace &lt;PathToTestResults&gt;, &lt;ContainerName&gt;, and &lt;LocalPathToStoreResults&gt; with the actual paths and names relevant to your project.

## GitHub Actions Workflow
The CI/CD pipeline is defined in .github/workflows/ci.yml.

##  Project Structure
```
Data_Quality_Testing/
│
├── data/                  # Data tables in JSON for BigQuery.
├── original_data/         # Original data tables.
├── src/                   # Scripts for BigQuery table and view setup.
├── test_helpers/          # Helper functions and classes.
├── tests/                 # Data quality test cases.
├── .env                   # Environment variables.
├── .gitignore             # Ignored files for version control.
├── Dockerfile             # Docker image definition.
├── docker-compose.yml     # Container orchestration.
├── requirements.txt       # Dependencies.
├── environment.py         # Environment configuration settings.
├── pytest.ini             # Pytest configuration.
└── README.md              # This README file.
```

## Results
View the Allure Report:  
[Allure Report](https://yurij-gor.github.io/Data_Quality_Testing/)