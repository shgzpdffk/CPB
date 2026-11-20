"""Локальная точка подключения поиска, базы и модели."""

import json
from pathlib import Path


def search_recipes(request):
    """Принимает products и необязательное wish, возвращает {"recipes": [...]}.

    Заглушка возвращает один и тот же тестовый ответ при любом запросе.
    Ответственный за поиск заменяет тело этой функции своей реализацией.
    Его код рассчитывает покупки и направленные замены с учётом контекста.
    Структура рецептов описана в search_fixture.json и проверяется клиентом.
    """
    fixture_path = Path(__file__).with_name("search_fixture.json")
    with fixture_path.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)
