import os
from dotenv import load_dotenv
import pytest
from environment import Environment


# Determine which file to load environment variables from
dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'docker.env') if os.getenv('RUN_IN_DOCKER') == 'true' else os.path.join(os.path.dirname(__file__), '..', '.env')
# Load environment variables from the specified file
load_dotenv(dotenv_path=dotenv_path)


# Pytest fixture for creating a BigQuery client and providing configuration
@pytest.fixture(scope="module")
def setup():
    env = Environment()  # Initialize our configuration
    bq_client = env.create_bq_client()  # Create a BigQuery client
    # Return the configuration instance along with the BigQuery client
    return bq_client, env
