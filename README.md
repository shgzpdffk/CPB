# Каталог рецептов CPB

`recipes.sqlite3` — готовая локальная база SQLite. В ней 10 000 рецептов и
107 050 шагов приготовления. Рецепты выбраны из одной доступной части выгрузки
«Поварёнка». Названия, ингредиенты, количества и полный текст шагов можно читать
офлайн. Ссылки на источник и изображение хранятся в отдельных столбцах.

## Как открыть базу

Из папки репозитория выполните:

```sh
sqlite3 -readonly recipes.sqlite3
```

В графическом SQLite-клиенте откройте тот же файл. В командной строке
`.tables` покажет список таблиц, `.schema recipes` — определение таблицы,
`.headers on` — заголовки столбцов, а `.quit` закроет консоль.

Из Python можно подключиться стандартным модулем `sqlite3`:

```python
import sqlite3
from contextlib import closing
from pathlib import Path

uri = Path("recipes.sqlite3").resolve().as_uri() + "?mode=ro"
with closing(sqlite3.connect(uri, uri=True)) as db:
    db.row_factory = sqlite3.Row
    rows = db.execute("SELECT recipe_id, title FROM recipes ORDER BY recipe_id LIMIT 10")
    for row in rows:
        print(row["recipe_id"], row["title"])
```

Для локальных правок сделайте копию файла. Откройте копию без `-readonly` и
включите внешние ключи командой `PRAGMA foreign_keys = ON;` на каждом соединении.
Шаги и ингредиенты удаляются каскадно при удалении рецепта, а разметка контекстов
удаляется вместе со строкой ингредиента.

## Структура базы

В таблицах ниже `NULL` означает, что значение отсутствует. Первичный ключ
однозначно определяет строку. Внешний ключ связывает её с записью в другой таблице.

### `recipes` — карточки рецептов

| Столбец | Тип | Значение |
|---|---|---|
| `recipe_id` | INTEGER | Первичный ключ, ID рецепта у источника |
| `page_url` | TEXT | Обязательная уникальная ссылка на оригинал |
| `title` | TEXT | Обязательное название |
| `description` | TEXT | Описание, может быть NULL |
| `main_image_url` | TEXT | Ссылка на главное изображение, может быть NULL |
| `cooking_time_raw` | TEXT | Время приготовления как в источнике, может быть NULL |
| `cooking_time_minutes` | INTEGER | Распознанное время в минутах, положительное число или NULL |
| `portions_raw` | TEXT | Количество порций как в источнике, может быть NULL |
| `uses_oven` | INTEGER | 1 — нужна духовка, 0 — можно без духовки, NULL — неизвестно |

### `recipe_steps` — пошаговые инструкции

| Столбец | Тип | Значение |
|---|---|---|
| `recipe_id` | INTEGER | Внешний ключ на `recipes.recipe_id` |
| `step_no` | INTEGER | Номер шага в исходном порядке, начиная с 1. Возможны пропуски после отсева пустых шагов |
| `step_text` | TEXT | Полный текст шага, обязательное поле |

Первичный ключ — пара `(recipe_id, step_no)`.

### `recipe_ingredients` — ингредиенты рецепта

| Столбец | Тип | Значение |
|---|---|---|
| `recipe_id` | INTEGER | Внешний ключ на `recipes.recipe_id` |
| `ingredient_no` | INTEGER | Номер строки ингредиента, начиная с 1 |
| `product_id` | INTEGER | Внешний ключ на `products.product_id` |
| `source_name` | TEXT | Обязательное название из выгрузки |
| `quantity_raw` | TEXT | Количество и единица в исходном виде, например `300 г` или `по вкусу`. Если количество отсутствует, хранится NULL |
| `is_required` | INTEGER | 1 — обязательный ингредиент, 0 — необязательный. При импорте используется 1 |

Первичный ключ — пара `(recipe_id, ingredient_no)`. Индекс
`(product_id, recipe_id)` ускоряет обратный поиск рецептов по продукту.

### `products` и `product_aliases` — справочник продуктов

| Таблица | Столбец | Тип | Значение |
|---|---|---|---|
| `products` | `product_id` | INTEGER | Локальный первичный ключ продукта |
| `products` | `product_key` | TEXT | Обязательное уникальное нормализованное название |
| `products` | `display_name` | TEXT | Обязательное название для отображения |
| `product_aliases` | `alias_key` | TEXT | Нормализованный вариант названия, первичный ключ |
| `product_aliases` | `product_id` | INTEGER | Внешний ключ на `products.product_id` |

При нормализации регистр приводится к нижнему, пробелы схлопываются, а «ё»
заменяется на «е». Например, «грудка куриная» указывает на «куриную грудку».
«Масло» и «масло сливочное» могут иметь разные ID.

### `cooking_contexts` и `recipe_ingredient_contexts` — условия приготовления

| Таблица | Столбец | Тип | Значение |
|---|---|---|---|
| `cooking_contexts` | `context_key` | TEXT | Первичный ключ контекста, например `cold_sauce` |
| `cooking_contexts` | `display_name` | TEXT | Обязательное название контекста |
| `recipe_ingredient_contexts` | `recipe_id` | INTEGER | ID рецепта, часть ссылки на строку ингредиента |
| `recipe_ingredient_contexts` | `ingredient_no` | INTEGER | Номер строки, вторая часть ссылки на `recipe_ingredients` |
| `recipe_ingredient_contexts` | `context_key` | TEXT | Внешний ключ на `cooking_contexts.context_key` |
| `recipe_ingredient_contexts` | `evidence` | TEXT | Обязательное пояснение, например номер шага, подтверждающего контекст |

Первичный ключ таблицы разметки — тройка `(recipe_id, ingredient_no, context_key)`.

### `substitution_rules` — допустимые замены

| Столбец | Тип | Значение |
|---|---|---|
| `required_product_id` | INTEGER | ID исходного продукта из `products` |
| `available_product_id` | INTEGER | ID продукта-замены из `products` |
| `context_key` | TEXT | Ключ из `cooking_contexts`. NULL означает замену без условия |
| `explanation` | TEXT | Обязательное пояснение замены |

Замены направленные. Правило «натуральный йогурт вместо сметаны в холодном
соусе» сработает, только если строка со сметаной размечена контекстом
`cold_sauce`. Пара продуктов и контекст задают уникальное правило. Признак
духовки и контексты для загруженных рецептов требуют отдельной разметки.

## Как прочитать рецепт

Сначала найдите нужный ID, затем подставьте его вместо `123`:

```sql
SELECT recipe_id, title FROM recipes ORDER BY recipe_id LIMIT 10;

SELECT title, description, cooking_time_minutes, portions_raw
FROM recipes WHERE recipe_id = 123;

SELECT i.ingredient_no, i.source_name, i.quantity_raw, p.display_name
FROM recipe_ingredients AS i
JOIN products AS p ON p.product_id = i.product_id
WHERE i.recipe_id = 123
ORDER BY i.ingredient_no;

SELECT step_no, step_text
FROM recipe_steps
WHERE recipe_id = 123
ORDER BY step_no;
```

## Как найти блюда по запасам

Запрос ниже работает в консоли SQLite 3.38 или новее. Сначала посмотрите ID
продуктов, затем замените `[1,2]` в параметре на список своих ID. Пустой список
задаётся как `[]`. Для фильтра без духовки установите `1`. Чтобы снять
ограничение по времени, замените `30` на `null`.

```text
SELECT product_id, display_name FROM products ORDER BY product_id LIMIT 20;
.parameter init
.parameter set :available_product_ids "'[1,2]'"
.parameter set :require_no_oven 0
.parameter set :max_cooking_minutes 30
```

Запрос учитывает только обязательные ингредиенты, проверяет допустимые замены
и возвращает рецепты, для которых нужно докупить не больше двух разных
продуктов. Списки покупок и замен возвращаются в JSON. Результаты отсортированы
по числу недостающих продуктов и ID рецепта.

```sql
WITH stock AS (
    SELECT value AS product_id FROM json_each(:available_product_ids)
),
eligible AS (
    SELECT recipe_id
    FROM recipes AS r
    WHERE (NOT :require_no_oven OR r.uses_oven = 0)
      AND (:max_cooking_minutes IS NULL OR r.cooking_time_minutes <= :max_cooking_minutes)
      AND EXISTS (SELECT 1 FROM recipe_steps WHERE recipe_id = r.recipe_id)
      AND EXISTS (SELECT 1 FROM recipe_ingredients WHERE recipe_id = r.recipe_id)
),
matches AS (
    SELECT ri.recipe_id, ri.ingredient_no, ri.product_id,
           replacement.available_product_id AS replacement_id,
           replacement.context_key, replacement.explanation
    FROM eligible AS r
    JOIN recipe_ingredients AS ri ON ri.recipe_id = r.recipe_id AND ri.is_required = 1
    LEFT JOIN substitution_rules AS replacement ON replacement.rowid = (
        SELECT sr.rowid
        FROM substitution_rules AS sr
        WHERE sr.required_product_id = ri.product_id
          AND sr.available_product_id IN (SELECT product_id FROM stock)
          AND (sr.context_key IS NULL OR EXISTS (
              SELECT 1
              FROM recipe_ingredient_contexts AS ric
              WHERE ric.recipe_id = ri.recipe_id
                AND ric.ingredient_no = ri.ingredient_no
                AND ric.context_key = sr.context_key
          ))
        ORDER BY sr.context_key IS NOT NULL, sr.available_product_id, sr.context_key
        LIMIT 1
    )
    WHERE ri.product_id NOT IN (SELECT product_id FROM stock)
)
SELECT r.recipe_id,
       count(DISTINCT m.product_id) FILTER (WHERE m.replacement_id IS NULL) AS missing_count,
       json_group_array(DISTINCT m.product_id)
           FILTER (WHERE m.product_id IS NOT NULL AND m.replacement_id IS NULL) AS missing_product_ids,
       json_group_array(json_object(
           'ingredient_no', m.ingredient_no,
           'required_product_id', m.product_id,
           'available_product_id', m.replacement_id,
           'context_key', m.context_key,
           'explanation', m.explanation
       )) FILTER (WHERE m.replacement_id IS NOT NULL) AS substitutions
FROM eligible AS r
LEFT JOIN matches AS m ON m.recipe_id = r.recipe_id
GROUP BY r.recipe_id
HAVING missing_count <= 2
ORDER BY missing_count, r.recipe_id;
```
