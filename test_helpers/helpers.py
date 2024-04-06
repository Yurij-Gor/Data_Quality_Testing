import allure


def execute_query_and_log(bq_client, query, description="Executing query", include_query_in_message=False):
    """Выполняет SQL-запрос и логирует его в Allure."""
    step_description = description
    if include_query_in_message:
        step_description += f"\n\nExecuted query:\n{query}"

    with allure.step(step_description):
        # Всегда прикрепляем SQL запрос как аттачмент к шагу в Allure
        allure.attach(query, name="SQL Query", attachment_type=allure.attachment_type.TEXT)

        query_job = bq_client.query(query)  # Выполнение запроса
        results = query_job.result()  # Получение результатов запроса
        return results
