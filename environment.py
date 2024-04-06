import os
from google.cloud import bigquery
from google.oauth2.service_account import Credentials


class Environment:
    def __init__(self):
        # Получаем обязательные переменные окружения, выбрасываем исключение, если они не установлены
        self.google_application_credentials = self._get_env_variable("GOOGLE_APPLICATION_CREDENTIALS")
        self.gcp_project_id = self._get_env_variable("GCP_PROJECT_ID")
        self.bigquery_dataset_id = self._get_env_variable("BIGQUERY_DATASET_ID")

    def _get_env_variable(self, var_name):
        """Получает переменную окружения, выбрасывает исключение, если она не установлена."""
        value = os.getenv(var_name)
        if value is None:
            raise ValueError(f"Environment variable {var_name} is not set")
        return value

    def create_bq_client(self):
        """Создает и возвращает клиента BigQuery, используя учетные данные из файла сервисного аккаунта."""
        credentials = Credentials.from_service_account_file(
            self.google_application_credentials)
        return bigquery.Client(credentials=credentials, project=self.gcp_project_id)

    def get_full_table_id(self, table_name):
        """Возвращает полный идентификатор таблицы в формате 'project.dataset.table'."""
        return f"{self.gcp_project_id}.{self.bigquery_dataset_id}.{table_name}"
