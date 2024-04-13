import allure
from test_helpers.helpers import execute_query_and_log


@allure.story('Data_Tables_Creation')
@allure.severity(allure.severity_level.CRITICAL)
@allure.description("""
Проверяет, что все модели устройств из таблицы agg_data имеют соответствующие записи в таблице device_segments.
Использует функцию UPPER() для игнорирования регистра символов.
""")
def test_device_models_match(setup):
    """
    Проверяет, что все модели устройств из таблицы agg_data имеют соответствующие записи в таблице device_segments.
    Использует функцию UPPER() для игнорирования регистра символов.
    """
    bq_client, env = setup
    agg_data = env.get_full_table_id('agg_data')
    device_segments = env.get_full_table_id('device_segments')

    query = f"""
        -- Выбор уникальных моделей устройств из таблицы agg_data после приведения их к верхнему регистру
        SELECT DISTINCT UPPER(agg.device_model) AS device_model_upper
        -- Указание таблицы agg_data, из которой будут выбираться данные, с использованием псевдонима 'agg'
        FROM `{agg_data}` agg
        -- Отбор моделей устройств, которых нет в таблице device_segments
        WHERE UPPER(agg.device_model) NOT IN (
          -- Подзапрос для выбора уникальных моделей устройств из таблицы device_segments после приведения их к верхнему регистру
          SELECT DISTINCT UPPER(ds.device_model)
          -- Указание таблицы device_segments, из которой будут выбираться данные для подзапроса, с использованием псевдонима 'ds'
          FROM `{device_segments}` ds
        )
    """

    # Используем нашу вспомогательную функцию для выполнения запроса и логирования его в Allure.
    results = execute_query_and_log(bq_client, query,
                                    "Проверка соответствия моделей устройств",
                                    include_query_in_message=False)

    # Преобразуем результаты в список для удобства работы с ними далее.
    missing_models = [row.device_model_upper for row in results]

    # Если найдены устройства в agg_data, отсутствующие в device_segments, выводим сообщение об ошибке.
    assert len(missing_models) == 0, f"Найдены устройства в agg_data, отсутствующие в device_segments:\n" + "\n".join(
        missing_models)


@allure.story('Data_Tables_Creation')
@allure.severity(allure.severity_level.CRITICAL)
@allure.description("""
Тест проверяет, что для всех app_name из таблицы app_names существует соответствие с app_short в таблице device_segments. Это гарантирует целостность данных между таблицами и правильность ссылок на приложения.
""")
def test_app_names_match(setup):
    """
    Тест проверяет, что для всех app_name из таблицы app_names существует соответствие с app_short в таблице device_segments.
    """
    bq_client, env = setup
    app_names = env.get_full_table_id('app_names')
    device_segments = env.get_full_table_id('device_segments')

    # Формирование SQL-запроса для проверки соответствия имен приложений
    query = f"""
        -- Выбираем уникальные названия приложений и платформы из таблицы app_names
        SELECT DISTINCT an.app_name, an.platform
        FROM `{app_names}` an
        -- Условие для отбора записей, для которых не существует соответствующих записей в таблице device_segments
        WHERE NOT EXISTS (
          -- Подзапрос, который проверяет наличие записи в device_segments
          SELECT 1
          FROM `{device_segments}` ds
          -- Условие соответствия между названием приложения и коротким названием приложения в таблице device_segments
          WHERE an.app_name = ds.app_short AND an.platform = ds.platform
        )
    """

    # Используем нашу вспомогательную функцию для выполнения запроса и логирования его в Allure.
    results = execute_query_and_log(bq_client, query, "Проверка соответствия названий приложений и платформ",
                                    include_query_in_message=False)

    # Сбор непрошедших проверку элементов
    failed_items = [(row.app_name, row.platform) for row in results]

    with allure.step("Проверка на отсутствие непрошедших проверку элементов"):
        assert not failed_items, "Найдены приложения в app_names без соответствия в device_segments:\n" + "\n".join(
            f"Название приложения: {app_name}, Платформа: {platform}" for app_name, platform in failed_items)


@allure.story('Data_Tables_Creation')
@allure.severity(allure.severity_level.NORMAL)
@allure.description("""
Тест проверяет наличие соответствующих записей в таблице device_segments для каждой записи в таблице agg_data, 
обеспечивая целостность данных о приложениях и устройствах.
""")
def test_missing_device_data(setup):
    """
    Проверка наличия соответствующих записей в таблице device_segments для каждой записи в таблице agg_data.
    """
    bq_client, env = setup
    agg_data = env.get_full_table_id('agg_data')
    app_names = env.get_full_table_id('app_names')
    device_segments = env.get_full_table_id('device_segments')

    query = f"""
        -- Выбираем данные о приложениях и моделях устройств
        SELECT agg.app_id, agg.device_model, an.app_name, an.platform
        -- Из таблицы agg_data, используя псевдоним 'agg'
        FROM `{agg_data}` agg
        -- Присоединяем таблицу app_names, используя псевдоним 'an', по app_id
        JOIN `{app_names}` an ON agg.app_id = an.app_id
        -- Левое соединение с таблицей device_segments, используя псевдоним 'ds', по модели устройства с учетом регистра
        LEFT JOIN `{device_segments}` ds ON UPPER(agg.device_model) = UPPER(ds.device_model)
            -- Также проверяем соответствие имени приложения и платформы между app_names и device_segments
            AND an.app_name = ds.app_short AND an.platform = ds.platform
        -- Условие, выбирающее записи, для которых нет соответствующей модели устройства в device_segments
        WHERE ds.device_model IS NULL
    """

    results = execute_query_and_log(bq_client, query, "Поиск данных без соответствий в device_segments",
                                    include_query_in_message=False)

    failed_items = [(row.app_id, row.device_model, row.app_name, row.platform) for row in results]

    with allure.step("Проверка на отсутствие записей без соответствующих моделей устройств в device_segments"):
        assert not failed_items, "Найдены записи в agg_data без соответствующих моделей устройств в device_segments:\n" + \
                                 "\n".join(
                                     f"App ID: {app_id}, Device Model: {device_model}, App Name: {app_name}, Platform: {platform}"
                                     for app_id, device_model, app_name, platform in failed_items)


@allure.story('Data_Tables_Creation')
@allure.severity(allure.severity_level.NORMAL)
@allure.description("""
Проверяет уникальность записей в таблице device_segments по сочетанию device_model и segment, гарантируя отсутствие дубликатов, что важно для целостности данных.
""")
def test_device_segments_uniqueness(setup):
    """
    Проверка на уникальность записей в таблице device_segments по сочетанию device_model и segment.
    """
    bq_client, env = setup
    device_segments = env.get_full_table_id('device_segments')

    query = f"""
        -- Поиск дубликатов по сочетанию device_model и segment
        -- Это помогает обеспечить, что каждая модель устройства и сегмент уникально идентифицированы в таблице
        SELECT device_model, segment, COUNT(*) as cnt
        FROM `{device_segments}`
        GROUP BY device_model, segment
        -- Фильтрация групп, в которых количество записей больше одной, что указывает на наличие дубликатов
        HAVING cnt > 1
    """

    results = execute_query_and_log(bq_client, query, "Поиск дубликатов в device_segments",
                                    include_query_in_message=False)

    duplicates = [(row.device_model, row.segment, row.cnt) for row in results]

    with allure.step("Проверка на отсутствие дубликатов в device_segments"):
        assert not duplicates, "Обнаружены дубликаты в device_segments:\n" + \
                               "\n".join(
                                   f"Модель устройства: {device_model}, Сегмент: {segment}, Количество: {cnt}"
                                   for device_model, segment, cnt in duplicates)


@allure.story('Data_Tables_Creation')
@allure.severity(allure.severity_level.CRITICAL)
@allure.description("""
Проверяет, что в таблице agg_data нет записей с датой установки приложения ранее 1 января 2020 года, обеспечивая 
актуальность и корректность данных.
""")
def test_agg_data_date_range(setup):
    """
    Проверка, что нет записей с датой установки приложения ранее 1 января 2020 года в таблице agg_data.
    """
    bq_client, env = setup
    agg_data = env.get_full_table_id('agg_data')

    # Формируем запрос для проверки, что нет записей с датой установки приложения ранее '2020-01-01'
    query = f"""
        -- Поиск записей в agg_data с датой установки ранее '2020-01-01'
        SELECT COUNT(*) as cnt
        FROM `{agg_data}`
        WHERE install_date < '2020-01-01'
    """

    # Используем нашу вспомогательную функцию для выполнения запроса и логирования его в Allure
    results = execute_query_and_log(bq_client, query, "Проверка диапазона дат установки приложений",
                                    include_query_in_message=False)

    # Получаем количество записей, выходящих за пределы заданного диапазона дат, и преобразуем результат запроса
    count_out_of_range = next(results).cnt

    # Проверяем, что нет установок приложений до '2020-01-01'
    with allure.step("Проверка на отсутствие установок приложений до '2020-01-01'"):
        assert count_out_of_range == 0, f"Обнаружены установки приложений до '2020-01-01': {count_out_of_range}"


@allure.story('Data_Tables_Creation')
@allure.severity(allure.severity_level.NORMAL)
@allure.description("""
Проверяет, что в таблице agg_data все значения колонки installs положительные, тем самым гарантируя, что данные 
по установкам приложений корректны и логически валидны.
""")
def test_agg_data_positive_installs(setup):
    """
    Проверка на то, что все значения installs в таблице agg_data положительные.
    """
    bq_client, env = setup
    agg_data = env.get_full_table_id('agg_data')

    query = f"""
        -- Поиск записей в agg_data с неположительным количеством установок (installs <= 0)
        SELECT COUNT(*) as cnt
        FROM `{agg_data}`
        WHERE installs <= 0
    """

    # Выполнение запроса и логирование в Allure
    results = execute_query_and_log(bq_client, query, "Поиск неположительных значений installs",
                                    include_query_in_message=False)

    # Извлечение количества записей с неположительными значениями installs
    count_non_positive = next(results).cnt

    with allure.step("Проверка на отсутствие неположительных значений installs в agg_data"):
        assert count_non_positive == 0, f"Обнаружены неположительные значения установок: {count_non_positive}"


@allure.story('Data_Tables_Creation')
@allure.severity(allure.severity_level.CRITICAL)
@allure.description("""
Проверяет наличие соответствия каждого app_id из таблицы agg_data в таблице app_names, обеспечивая целостность ссылочных 
данных между таблицами.
""")
def test_app_names_consistency(setup):
    """
    Проверка соответствия app_id между таблицами agg_data и app_names.
    Этот тест гарантирует, что все app_id, использованные в agg_data, корректно определены и присутствуют в app_names.
    """
    bq_client, env = setup
    agg_data = env.get_full_table_id('agg_data')
    app_names = env.get_full_table_id('app_names')

    query = f"""
        -- Выполняется LEFT JOIN между таблицей agg_data и app_names по столбцу app_id.
        -- Это позволяет нам проверить каждый app_id из agg_data на наличие соответствующей записи в app_names.
        -- Если соответствующая запись в app_names не найдена (т.е., результат JOIN'a для этой строки будет NULL),
        -- такие app_id считаются "отсутствующими" в app_names.
        SELECT ad.app_id
        FROM `{agg_data}` ad
        LEFT JOIN `{app_names}` an ON ad.app_id = an.app_id
        WHERE an.app_id IS NULL  -- Отбираются только те app_id, для которых не нашлось соответствия в app_names.
    """

    # Выполнение запроса и логирование в Allure
    missing_app_ids = execute_query_and_log(bq_client, query,
                                            "Проверка соответствия app_id между agg_data и app_names",
                                            include_query_in_message=False)

    # Преобразуем результаты в список app_id для удобства ассерта
    missing_app_ids_list = [row.app_id for row in missing_app_ids]

    with allure.step("Проверка на отсутствие app_id из agg_data без соответствующих записей в app_names"):
        assert not missing_app_ids_list, f"Обнаружены app_id из agg_data, отсутствующие в app_names: {', '.join(missing_app_ids_list)}"


@allure.story('Data_Tables_Creation')
@allure.severity(allure.severity_level.NORMAL)
@allure.description("""
Проверяет таблицу app_names на отсутствие дубликатов app_id, где один и тот же app_id ассоциирован с разными app_name 
или platform. 
""")
def test_app_names_no_duplicate_ids(setup):
    """
    Проверка на отсутствие дубликатов app_id с различными app_name или platform в таблице app_names.
    """
    bq_client, env = setup
    app_names = env.get_full_table_id('app_names')

    # Формируем SQL-запрос для поиска дубликатов app_id, ассоциированных с различными app_name или platform.
    query = f"""
        SELECT app_id, COUNT(DISTINCT app_name) as unique_app_names, COUNT(DISTINCT platform) as unique_platforms
        FROM `{app_names}`
        GROUP BY app_id
        -- Группируем записи по app_id для агрегации данных. Это позволяет нам подсчитать количество
        -- уникальных app_name и platform, ассоциированных с каждым app_id.
        -- Условие HAVING применяется после группировки для фильтрации групп, у которых
        -- количество уникальных app_name или platform превышает 1. Это указывает на наличие дубликатов:
        -- ситуаций, когда одному идентификатору приложения соответствуют несколько названий или платформ.
        HAVING unique_app_names > 1 OR unique_platforms > 1
    """

    # Используем вспомогательную функцию для выполнения запроса и логирования его в Allure
    duplicates = execute_query_and_log(bq_client, query,
                                       "Поиск дубликатов app_id с различными app_name или platform",
                                       include_query_in_message=False)

    # Преобразуем результаты запроса в список для удобства последующей проверки.
    # Каждый элемент списка содержит app_id и количество уникальных значений app_name и platform для данного app_id.
    duplicate_details = [(row.app_id, row.unique_app_names, row.unique_platforms) for row in duplicates]

    with allure.step("Проверка на отсутствие дубликатов app_id с различными app_name или platform"):
        assert not duplicate_details, f"Обнаружены app_id с множественными app_names или platforms: {duplicate_details}"


@allure.story('Data_Tables_Creation')
@allure.severity(allure.severity_level.CRITICAL)
@allure.description("""
Проверяет согласованность между именами приложений и платформами в таблицах app_names и device_segments. 
Это обеспечивает, что каждое приложение и соответствующая платформа корректно отражены в обеих таблицах, 
поддерживая целостность данных.
""")
def test_app_names_platform_consistency(setup):
    """
    Тест проверяет, что каждое имя приложения и соответствующая платформа из таблицы app_names
    имеют соответствие в таблице device_segments.
    """
    bq_client, env = setup
    app_names = env.get_full_table_id('app_names')
    device_segments = env.get_full_table_id('device_segments')

    # Запрос на проверку соответствия имен приложений и платформ между таблицами app_names и device_segments.
    query = f"""
        -- Запрос на проверку соответствия имен приложений и платформ между таблицами app_names и device_segments.
        -- Используется LEFT JOIN для связи записей из app_names с соответствующими записями в device_segments.
        -- Условие ON an.app_name = ds.app_short AND an.platform = ds.platform гарантирует, что сопоставление идет по обоим ключевым полям.
        -- Условие WHERE ds.app_short IS NULL OR ds.platform IS NULL фильтрует те случаи, когда соответствующие записи в device_segments отсутствуют,
        -- указывая на несогласованность между таблицами.        
        SELECT an.app_name, an.platform
        FROM `{app_names}` an
        LEFT JOIN `{device_segments}` ds ON an.app_name = ds.app_short AND an.platform = ds.platform
        WHERE ds.app_short IS NULL OR ds.platform IS NULL
    """

    # Используем нашу вспомогательную функцию для выполнения запроса и логирования его в Allure.
    inconsistencies = execute_query_and_log(bq_client, query,
                                            "Проверка согласованности имен приложений и платформ",
                                            include_query_in_message=False)

    # Преобразуем результаты запроса в список для удобства последующей проверки.
    inconsistencies_details = [(row.app_name, row.platform) for row in inconsistencies]

    with allure.step("Проверка на отсутствие несогласованных имен приложений и платформ"):
        assert not inconsistencies_details, "Обнаружены несогласованные имена приложений или платформы между app_names и device_segments: " + \
                                            ", ".join(f"app_name: {app_name}, platform: {platform}" for app_name, platform in
                                                      inconsistencies_details)
