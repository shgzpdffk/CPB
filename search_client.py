from local_search import search_recipes


def validate_recipe(recipe):
    if not isinstance(recipe, dict):
        raise ValueError("Каждый рецепт должен быть объектом JSON")

    field_types = {
        "id": str,
        "title": str,
        "missing_count": int,
        "missing_required": list,
        "substitutions": list,
        "ingredients": list,
        "steps": list,
        "source_url": str,
    }

    for field, expected_type in field_types.items():
        if type(recipe.get(field)) is not expected_type:
            raise ValueError(
                f"В рецепте отсутствует или неверно заполнено поле {field}"
            )

    if recipe["missing_count"] < 0:
        raise ValueError("Число покупок не может быть отрицательным")

    if recipe["missing_count"] != len(recipe["missing_required"]):
        raise ValueError("Число покупок не совпадает со списком")

    for ingredient in recipe["ingredients"]:
        if not isinstance(ingredient, dict):
            raise ValueError("Ингредиент должен быть объектом JSON")

        if not isinstance(ingredient.get("name"), str):
            raise ValueError("У ингредиента должно быть название")

        count = ingredient.get("count")
        if count is not None and not isinstance(count, str):
            raise ValueError("Количество должно быть строкой или null")

    for substitution in recipe["substitutions"]:
        if not isinstance(substitution, dict):
            raise ValueError("Замена должна быть объектом JSON")

        for field in ("required_ingredient", "available_ingredient"):
            if not isinstance(substitution.get(field), str):
                raise ValueError(f"У замены неверно заполнено поле {field}")

        context = substitution.get("context")
        if context is not None and not isinstance(context, str):
            raise ValueError("Контекст замены должен быть строкой или null")

    for field in ("missing_required", "steps"):
        for text in recipe[field]:
            if not isinstance(text, str):
                raise ValueError(f"Список {field} должен содержать строки")

def validate_search_response(response):
    if not isinstance(response, dict):
        raise ValueError("Ответ поиска должен быть JSON")

    if not isinstance(response.get("recipes"), list):
        raise ValueError("Нужен список recipes")

    for recipe in response["recipes"]:
        validate_recipe(recipe)

    return response

def fetch_recipes(request):
    response = search_recipes(request)
    return validate_search_response(response)
