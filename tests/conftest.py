import os
from dotenv import load_dotenv
import pytest
from environment import Environment


# Определяем, из какого файла загружать переменные окружения
dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'docker.env') if os.getenv('RUN_IN_DOCKER') == 'true' else os.path.join(os.path.dirname(__file__), '..', '.env')
# Загружаем переменные окружения из указанного файла
load_dotenv(dotenv_path=dotenv_path)


# Фикстура pytest для создания клиента BigQuery и предоставления конфигурации
@pytest.fixture(scope="module")
def setup():
    env = Environment()  # Инициализируем нашу конфигурацию
    bq_client = env.create_bq_client()  # Создаем клиента BigQuery
    # Теперь возвращаем экземпляр конфигурации вместе с клиентом BigQuery
    return bq_client, env
