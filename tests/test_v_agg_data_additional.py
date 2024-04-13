import allure
from test_helpers.helpers import execute_query_and_log


@allure.severity(allure.severity_level.CRITICAL)
@allure.description("Тестирование того, что даты установки приложений находятся в ожидаемом диапазоне.")
@allure.story('View_Creation')
def test_date_range(setup):
    """
    Тестирование, что даты установки приложений находятся в ожидаемом диапазоне.
    """
    bq_client, env = setup  # Используем фикстуру setup для получения клиента BigQuery и конфигурации
    v_agg_data = env.get_full_table_id('v_agg_data')  # Получаем полный ID таблицы v_agg_data
    start_date = "2020-01-01"

    # Формируем запрос для проверки диапазона дат
    query = f"""
    -- Выборка записей с датами установки за пределами ожидаемого диапазона
    -- Условие проверяет, что дата установки не раньше '{start_date}' и не позднее текущей даты
    SELECT COUNT(*) as cnt
    FROM `{v_agg_data}`
    WHERE install_date < '{start_date}' OR install_date > CURRENT_DATE()
    """

    # Используем вспомогательную функцию для выполнения запроса и логирования в Allure
    results = execute_query_and_log(bq_client, query, "Проверка дат установки в ожидаемом диапазоне",
                                    include_query_in_message=False)
    count_out_of_range = next(results).cnt  # Получаем количество записей за пределами диапазона

    # Проверка, что нет записей с датами установки вне заданного диапазона
    with allure.step(f"Проверка, что нет записей с датами установки вне диапазона после {start_date} и до текущей даты"):
        assert count_out_of_range == 0, f"Найдены установки с датами вне диапазона после {start_date} и до текущей даты"


@allure.story('View_Creation')
@allure.severity(allure.severity_level.NORMAL)
@allure.description("""
Тестирование согласованности типов данных в столбце installs представления v_agg_data. 
Проверяется, что все значения являются числовыми и корректно приводятся к типу INT64.
""")
def test_data_type_consistency(setup):
    """
    Тестирование согласованности типов данных для вьюхи v_agg_data.
    """
    bq_client, env = setup
    v_agg_data = env.get_full_table_id('v_agg_data')

    # Формируем SQL запрос для проверки, что все значения в столбце installs могут быть безопасно приведены к типу INT64
    # и не содержат некорректные данные.
    query_installs = f"""
        -- Проверка согласованности типов данных столбца installs в представлении v_agg_data
        -- Выбираем записи, где приведение installs к INT64 возвращает NULL, указывая на некорректные данные
        SELECT install_date, installs
        FROM `{v_agg_data}`
        WHERE SAFE_CAST(installs AS INT64) IS NULL
    """

    # Используем вспомогательную функцию для выполнения запроса и логирования его в Allure.
    results = execute_query_and_log(bq_client, query_installs, "Проверка типов данных столбца installs",
                                    include_query_in_message=False)

    # Собираем список записей с потенциально некорректными значениями installs.
    """ 
    Проходимся по каждой строке результата запроса. Для каждой строки создаем кортеж, содержащий дату установки 
    (install_date) и количество установок (installs). Для доступа к атрибуту 'installs' используем функцию getattr(), 
    которая позволяет безопасно получить значение атрибута по его имени (в данном случае 'installs'). 
    Если атрибут 'installs' отсутствует в строке (что не должно происходить, но проверка на всякий случай), функция 
    вернет значение None. Таким образом, failed_installs будет содержать список кортежей, каждый из которых 
    соответствует строке в результате запроса, где количество установок не удалось привести к типу INT64 
    (то есть, где условие SAFE_CAST(installs AS INT64) IS NULL истинно).Это список записей, которые потенциально 
    содержат некорректные данные в столбце installs.
    """
    failed_installs = [(row.install_date, getattr(row, 'installs', None)) for row in results]

    # Проверяем, что список failed_installs пуст, что означает отсутствие некорректных типов данных в installs.
    with allure.step("Проверка на отсутствие записей с некорректными типами данных в installs"):
        assert len(failed_installs) == 0, f"Найдены записи с некорректными значениями installs: {failed_installs}"


@allure.severity(allure.severity_level.CRITICAL)
@allure.description("""
Тестирование на наличие неправдоподобно высоких значений установок в представлении v_agg_data. 
Проверяется, что для всех приложений суммарное количество установок не превышает установленный порог.
""")
@allure.story('View_Creation')
def test_unrealistic_high_installs(setup):
    """
    Тестирование на наличие неправдоподобно высоких значений установок.
    """
    bq_client, env = setup
    v_agg_data = env.get_full_table_id('v_agg_data')
    threshold = 1000000  # условный порог для определения неправдоподобно высоких значений

    # Формируем запрос для подсчета суммарного количества установок для каждого приложения и фильтрации тех,
    # чье количество установок превышает установленный порог.
    query = f"""
        -- Подсчет суммарного количества установок для каждого приложения
        SELECT app_name, SUM(installs) as total_installs
        FROM `{v_agg_data}`
        -- Группировка по названию приложения
        GROUP BY app_name
        -- Фильтрация приложений, суммарное количество установок которых превышает установленный порог
        HAVING total_installs > {threshold}
    """

    # Используем нашу вспомогательную функцию для выполнения запроса и логирования его в Allure.
    results = execute_query_and_log(bq_client, query,
                                    f"Проверка наличия неправдоподобно высоких значений установок, порог: {threshold}",
                                    include_query_in_message=False)

    # Преобразуем результаты в список для подсчета их количества
    excessive_installs = [(row.app_name, row.total_installs) for row in results]

    # Проверяем, что нет приложений с установками, превышающими установленный порог.
    with allure.step(f"Проверка, что нет приложений с установками превышающими {threshold}"):
        assert len(excessive_installs) == 0, (f"Найдены приложения с неправдоподобно высокими значениями установок: "
                                              f"{excessive_installs}")


@allure.story('View_Creation')
@allure.severity(allure.severity_level.NORMAL)
@allure.description("""
Тест проверяет наличие установок приложений с неопределенной моделью устройства в представлении v_agg_data.
""")
def test_undefined_device_model_installs(setup):
    """
    Тестирование наличия установок приложений с неопределенной моделью устройства.
    """
    bq_client, env = setup
    v_agg_data = env.get_full_table_id('v_agg_data')

    # Сформируем запрос для выборки имен приложений и подсчета установок, где модель устройства не указана или является пустой строкой.
    query = f"""
        -- Выборка имен приложений и подсчет установок, где модель устройства не указана или пустая строка
        SELECT app_name, COUNT(*) as total_installs
        FROM `{v_agg_data}`
        WHERE device_model IS NULL OR device_model = ''
        GROUP BY app_name
    """

    # Используем вспомогательную функцию для выполнения запроса и логирования его в Allure.
    results = execute_query_and_log(bq_client, query, "Поиск установок с неопределенной моделью устройства",
                                    include_query_in_message=False)

    # Преобразуем результаты запроса в список кортежей для дальнейшего анализа.
    undefined_device_model_installs = [(row.app_name, row.total_installs) for row in results]

    # Если найдены установки с неопределенной моделью устройства, составляем сообщение об ошибке с деталями.
    if len(undefined_device_model_installs) > 0:
        error_message = "Обнаружены установки приложений с неопределенной моделью устройства:\n"
        for app_name, total_installs in undefined_device_model_installs:
            error_message += f"Приложение: {app_name}, Количество установок: {total_installs}\n"
        assert False, error_message
    else:
        assert True, "Не найдены установки с неопределенной моделью устройства."


@allure.story('View_Creation')
@allure.severity(allure.severity_level.CRITICAL)
@allure.description("""
Проверяет, что каждый сегмент устройства из v_agg_data существует в device_segments или помечен как 'non_target_device'.
""")
def test_v_agg_data_segment_existence(setup):
    """
    Проверяет, что каждый сегмент устройства из v_agg_data существует в device_segments или помечен как 'non_target_device'.
    """
    bq_client, env = setup
    v_agg_data = env.get_full_table_id('v_agg_data')
    device_segments = env.get_full_table_id('device_segments')

    # Формируем запрос для проверки существования каждого сегмента устройства из представления v_agg_data в таблице device_segments,
    # исключая сегмент 'non_target_device'. Этот запрос использует подзапрос с EXISTS для проверки наличия соответствующего сегмента в device_segments.
    query = f"""
        -- Выборка уникальных сегментов устройства из представления v_agg_data
        SELECT DISTINCT v.device_segment
        FROM `{v_agg_data}` v
        -- Фильтрация сегментов, отличных от 'non_target_device', и проверка их наличия в device_segments
        WHERE v.device_segment <> 'non_target_device' AND NOT EXISTS (
            -- Подзапрос проверяет наличие сегмента из v_agg_data в таблице device_segments.
            -- 'SELECT 1' используется для проверки существования записи: возвращает 1, если запись найдена.
            SELECT 1
            FROM `{device_segments}` ds
            WHERE v.device_segment = ds.segment
        )
    """
    # Выполнение запроса и логирование его в Allure с помощью функции execute_query_and_log.
    results = execute_query_and_log(bq_client, query, "Проверка существования сегментов устройства",
                                    include_query_in_message=False)

    # Преобразуем результаты запроса в список отсутствующих сегментов устройства.
    missing_segments = [row.device_segment for row in results]

    # Если найдены отсутствующие сегменты, составляем сообщение об ошибке.
    assert len(missing_segments) == 0, f"Найдены отсутствующие сегменты устройств в v_agg_data, которых нет в device_segments: {missing_segments}"
