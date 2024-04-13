import allure
import json
from datetime import date, datetime
from google.cloud.exceptions import GoogleCloudError


def execute_query_and_log(bq_client, query, description="Executing query", include_query_in_message=False):
    """Выполняет SQL-запрос и логирует его в Allure с дополнительной обработкой ошибок."""
    step_description = description
    if include_query_in_message:
        step_description += f"\n\nExecuted query:\n{query}"

    with allure.step(step_description):
        try:
            # Логирование SQL запроса
            allure.attach(query, name="SQL Query", attachment_type=allure.attachment_type.TEXT)

            query_job = bq_client.query(query)  # Выполнение запроса
            results = query_job.result()  # Получение результатов запроса
            results_list = list(results)  # Преобразуем результаты в список для многократного использования

            # Дополнительно логируем результаты запроса в JSON формате
            results_data = [dict(row.items()) for row in results_list]

            def default_serializer(obj):
                """JSON serializer for objects not serializable by default json code"""
                if isinstance(obj, (date, datetime)):
                    return obj.isoformat()
                raise TypeError("Type %s not serializable" % type(obj))

            results_json = json.dumps(results_data, indent=4, default=default_serializer)
            allure.attach(results_json, name="SQL Results", attachment_type=allure.attachment_type.JSON)

            return iter(results_list)  # Возвращаем итератор списка результатов

        except GoogleCloudError as e:
            allure.attach(str(e), name="Query Error", attachment_type=allure.attachment_type.TEXT)
            raise RuntimeError(f"Query execution failed: {e}")
        except Exception as e:
            allure.attach(str(e), name="General Error", attachment_type=allure.attachment_type.TEXT)
            raise RuntimeError(f"An error occurred: {e}")
