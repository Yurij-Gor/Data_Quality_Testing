import allure
from test_helpers.helpers import execute_query_and_log


# Тест на проверку отсутствия установок приложений до 1 января 2020 года
@allure.severity(allure.severity_level.CRITICAL)
@allure.description("Тестирование, что нет установок приложений до 1 января 2020 года.")
@allure.story('View_Creation')
def test_install_date_post_2020(setup):
    """Тестирование, что нет установок приложений до 1 января 2020 года."""
    bq_client, env = setup  # Распаковываем возвращаемые значения фикстуры
    v_agg_data = env.get_full_table_id('v_agg_data')  # Получаем полный ID таблицы v_agg_data
    query = f"""
        -- Вычисляем количество записей, у которых дата установки приложения меньше 1 января 2020 года
        SELECT COUNT(*) as cnt
        -- Из таблицы v_agg_data,
        FROM `{v_agg_data}`
        -- Условие для фильтрации записей по дате установки
        WHERE install_date < '2020-01-01'
    """

    # Используем вспомогательную функцию для выполнения SQL-запроса и логирования в Allure
    results = execute_query_and_log(bq_client, query, "Проверка отсутствия установок до 1 января 2020 года", include_query_in_message=False)
    for row in results:
        with allure.step(f"Проверка, что количество установок = 0, фактически получено: {row.cnt}"):
            assert row.cnt == 0, "Should be 0 installations before 2020-01-01"  # Проверка условия теста


# Тест на проверку отсутствия установок с нулевым или отрицательным количеством
@allure.severity(allure.severity_level.CRITICAL)
@allure.description("Тестирование, что нет установок с нулевым или отрицательным количеством.")
@allure.story('View_Creation')
def test_positive_installs(setup):
    """Тестирование, что нет установок с нулевым или отрицательным количеством."""
    bq_client, env = setup  # Распаковываем возвращаемые значения фикстуры
    v_agg_data = env.get_full_table_id('v_agg_data')  # Получаем полный ID таблицы v_agg_data
    query = f"""
        -- Подсчет количества записей, где количество установок меньше или равно нулю
        SELECT COUNT(*) as cnt
        -- Обращение к таблице v_agg_data
        FROM `{v_agg_data}`
        -- Условие фильтрации записей по количеству установок
        WHERE installs <= 0
    """

    # Используем вспомогательную функцию для выполнения SQL-запроса и логирования в Allure
    results = execute_query_and_log(bq_client, query,
                                    "Проверка на отсутствие установок с нулевым или отрицательным количеством",
                                    include_query_in_message=False)
    for row in results:
        with allure.step(f"Проверка, что количество установок > 0, фактически получено: {row.cnt}"):
            assert row.cnt == 0, "Should be 0 installations with non-positive numbers"  # Проверка условия теста


# Тест на проверку отсутствия записей с нецелевыми сегментами устройств
@allure.story('View_Creation')
@allure.severity(allure.severity_level.NORMAL)
@allure.description("""
Тест проверяет отсутствие записей с нецелевыми сегментами устройств в представлении v_agg_data. 
Нецелевые сегменты - это те, которые не указаны или явно обозначены как 'non_target_device'.
""")
def test_non_target_device_segments_absent(setup):
    bq_client, env = setup  # Распаковываем возвращаемые значения фикстуры
    v_agg_data = env.get_full_table_id('v_agg_data')  # Получаем полный ID таблицы v_agg_data
    detailed_query = f"""
        -- Выбор модели устройства и сегмента устройства из вьюхи v_agg_data
        SELECT device_model, device_segment
        FROM `{v_agg_data}`
        -- Условие фильтрации для поиска записей, где сегмент устройства не указан (NULL)
        -- или явно указан как 'non_target_device'. Это условие помогает найти
        -- нецелевые сегменты устройств, которые потенциально могут представлять
        -- интерес для анализа или требовать дополнительных действий по коррекции данных.
        WHERE device_segment IS NULL OR device_segment = 'non_target_device'
    """

    # Используем вспомогательную функцию для выполнения SQL-запроса и логирования в Allure
    detailed_results = execute_query_and_log(bq_client, detailed_query,
                                             "Проверка отсутствия нецелевых сегментов устройств",
                                             include_query_in_message=False)

    detailed_failures = []
    with allure.step("Сбор нецелевых сегментов устройств"):
        for row in detailed_results:
            if row.device_segment is None or row.device_segment == 'non_target_device':
                detailed_failures.append((row.device_model, row.device_segment or 'NULL'))

    with allure.step("Проверка, что не найдены нецелевые сегменты устройств"):
        assert len(
            detailed_failures) == 0, f"Expected 0 non-target device segments, found: {len(detailed_failures)}\n" + \
                                     "\n".join(f"Device Model: {model}, Segment: {segment}" for model, segment in
                                               detailed_failures)


@allure.story('View_Creation')
@allure.severity(allure.severity_level.NORMAL)
@allure.description("""
Проверяет отсутствие дубликатов в представлении v_agg_data. Дубликаты могут указывать на проблемы в процессе сбора или обработки данных.
""")
def test_no_duplicates_in_view(setup):
    """
    Проверка на отсутствие дубликатов в вьюхе v_agg_data.
    """
    bq_client, env = setup  # Распаковываем возвращаемые значения фикстуры
    v_agg_data = env.get_full_table_id('v_agg_data')  # Получаем полный ID таблицы v_agg_data

    # Формируем SQL запрос для проверки наличия дубликатов в данных
    query = f"""
        SELECT app_name, device_model, install_date, installs, device_segment, COUNT(*) as cnt
        FROM `{v_agg_data}`  -- Из представления v_agg_data
        GROUP BY app_name, device_model, install_date, installs, device_segment  -- Группировка по ключевым полям
        HAVING cnt > 1  -- Условие для отбора групп с количеством записей больше одной (дубликаты)
    """

    # Используем вспомогательную функцию для выполнения SQL-запроса и логирования в Allure
    results = execute_query_and_log(bq_client, query,
                                    "Проверка наличия дубликатов в представлении v_agg_data",
                                    include_query_in_message=False)

    # Собираем найденные дубликаты в список для удобства отображения в сообщении об ошибке
    duplicate_records = []
    with allure.step("Сбор информации о найденных дубликатах"):
        for row in results:
            duplicate_records.append(
                (row.app_name, row.device_model, row.install_date, row.installs, row.device_segment, row.cnt))

    # Проверяем, что список найденных дубликатов пуст, иначе фиксируем нарушение
    with allure.step("Проверка, что дубликаты отсутствуют"):
        assert len(duplicate_records) == 0, "Найдены дубликаты в вьюхе:\n" + "\n".join(
            f"Приложение: {record[0]}, Модель устройства: {record[1]}, Дата установки: {record[2]}, Установки: {record[3]}, Сегмент устройства: {record[4]}, Количество: {record[5]}"
            for record in duplicate_records
        )


@allure.story('View_Creation')
@allure.severity(allure.severity_level.CRITICAL)
@allure.description("""
Проверка соответствия указанных сегментов устройств в представлении v_agg_data с сегментами, присутствующими в таблице device_segments.
""")
def test_v_agg_data_proper_segment_use(setup):
    """
    Проверка соответствия сегментов устройств между v_agg_data и device_segments.
    Этот тест удостоверяется, что каждый сегмент устройства, указанный в представлении v_agg_data,
    существует в таблице device_segments, кроме случая сегмента 'non_target_device',
    который является допустимым значением по умолчанию.
    """

    # Инициализация клиента BigQuery и получение идентификаторов таблиц
    bq_client, env = setup
    v_agg_data = env.get_full_table_id('v_agg_data')
    device_segments = env.get_full_table_id('device_segments')

    # SQL-запрос для проверки наличия каждого сегмента устройства из v_agg_data в таблице device_segments
    query = f"""
    SELECT 
      v.device_model, 
      v.device_segment,
      CASE 
        WHEN d.device_model IS NULL THEN 'Missing'  -- Если нет соответствия в таблице device_segments, ставим статус 'Missing'
        ELSE 'Present'  -- Если есть соответствие, ставим статус 'Present'
      END AS segment_status
    FROM (
      SELECT DISTINCT device_model, device_segment
      FROM `{v_agg_data}`  -- Выбираем уникальные пары модель устройства и сегмент из v_agg_data
      WHERE device_segment != 'non_target_device'  -- Исключаем сегмент 'non_target_device', так как он не требует проверки
    ) AS v
    LEFT JOIN `{device_segments}` AS d  -- Присоединяем таблицу device_segments
    ON v.device_model = d.device_model AND v.device_segment = d.segment  -- Условие присоединения: совпадение модели и сегмента
    """

    # Выполнение запроса и логирование его в Allure
    segment_checks = execute_query_and_log(bq_client, query, "Проверка соответствия сегментов устройств",
                                           include_query_in_message=False)

    # Сбор и проверка результатов
    missing_segments = [(row.device_model, row.device_segment) for row in segment_checks if row.segment_status == 'Missing']

    # Ассерт на отсутствие отсутствующих сегментов
    with allure.step("Проверка на отсутствие недостающих сегментов устройств"):
        assert not missing_segments, f"Найдены отсутствующие сегменты устройств в device_segments: {missing_segments}"


@allure.story('View_Creation')
@allure.severity(allure.severity_level.CRITICAL)
@allure.description("""
Проверка использования 'non_target_device' в представлении v_agg_data только в случаях отсутствия сегментов устройств в таблице device_segments.
""")
def test_non_target_device_usage(setup):
    """
    Проверка корректности использования 'non_target_device' в v_agg_data.
    Этот тест проверяет, что 'non_target_device' используется только когда нет соответствующих сегментов в device_segments.
    Если модели устройств есть в device_segments, использование 'non_target_device' считается ошибочным.
    """
    bq_client, env = setup  # Распаковываем возвращаемые значения фикстуры
    v_agg_data = env.get_full_table_id('v_agg_data')  # Получаем полный ID таблицы v_agg_data
    device_segments = env.get_full_table_id('device_segments')  # Получаем полный идентификатор таблицы device_segments

    # Формирование запроса для выборки моделей устройств с 'non_target_device' и проверка на их наличие в device_segments.
    query = f"""
    -- Выборка моделей устройств, помеченных как 'non_target_device', и проверка на их наличие в таблице device_segments.
    -- В случае если модель присутствует в device_segments, это указывает на ошибочное использование метки 'non_target_device'.
    SELECT 
      v.device_model, 
      STRING_AGG(d.segment) AS expected_segments  -- Агрегируем все сегменты, связанные с моделью устройства, в строку.
    FROM (
      SELECT DISTINCT device_model  -- Выборка уникальных моделей устройств с меткой 'non_target_device' из v_agg_data.
      FROM `{v_agg_data}`
      WHERE device_segment = 'non_target_device'
    ) v
    LEFT JOIN `{device_segments}` d ON v.device_model = d.device_model  -- Соединяем с таблицей device_segments для проверки наличия модели.
    GROUP BY v.device_model
    HAVING COUNT(d.segment) > 0  -- Отбираем только те случаи, где модель имеет хотя бы один сегмент в device_segments.
    """

    # Выполнение запроса и логирование в Allure.
    results = execute_query_and_log(bq_client, query,
                                    "Проверка некорректного использования 'non_target_device'",
                                    include_query_in_message=False)

    # Сбор информации о моделях и сегментах для сообщения об ошибке.
    incorrect_models = []
    for row in results:
        incorrect_models.append(f"Модель: '{row.device_model}', Ожидаемые сегменты: [{row.expected_segments}]")

    # Ассерт, проверяющий, что не найдены модели устройств, ошибочно помеченные как 'non_target_device'.
    assert not incorrect_models, "Обнаружено некорректное использование 'non_target_device':\n" + "\n".join(incorrect_models)
