import requests
from pydantic import BaseModel, ConfigDict, Field
import json
SYSTEM_PROMPT = """
Извлеки строгий верхний предел времени приготовления.
Верни только JSON с полем max_cooking_minutes.
Значение — положительное целое число минут или null.
Если вводят число в секундах или часах переводи в минуты

Переводи часы в минуты.
Если строгого ограничения нет или оно отменено, верни null.
Не придумывай предел из слов «быстро» или «желательно».

Примеры:
«До 25 минут» -> {"max_cooking_minutes":25}
«Не дольше получаса» -> {"max_cooking_minutes":30}
«Максимум полтора часа» -> {"max_cooking_minutes":90}
«Желательно за 20 минут, но могу подождать» -> {"max_cooking_minutes":null}
«Хочу быстрый ужин» -> {"max_cooking_minutes":null}
«Хотел до 20 минут, но теперь время неважно» -> {"max_cooking_minutes":null}
"""

# класс для установки ограничений
#класс бейсмодел - мы от неё наследуем, екстра запрещает лишние поля а стрикт делает проверку строгим
class ParsedPrefer(BaseModel):

    model_config = ConfigDict(extra="forbid", strict=True)
    max_cooking_minutes :int |None = Field(gt = 0)
# класс вызывающийся гуи
def parse(text: str) -> ParsedPrefer:
    if not text.strip():
        return ParsedPrefer()
# тут запрос оламе
    response = requests.post(
        "http://127.0.0.1:11434/api/chat",
        json={
            "model": "recipe-parser",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            "format": ParsedPrefer.model_json_schema(),
            "stream": False,
            "options": {"temperature": 0},
        },
    )
    response.raise_for_status()
    
    ollama_response = response.json()
    content = ollama_response["message"]["content"]

    return ParsedPrefer.model_validate_json(content)

print(parse("хочу ужин до 3 часа готовки"))