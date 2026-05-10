import json
import logging
import httpx
import os
import re
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

logger = logging.getLogger(__name__)


def extract_first_json(text: str) -> str:
    """Извлекает первый корректный JSON из строки. Пытается исправить незакрытые скобки."""
    # Удаляем markdown-обёртки
    text = re.sub(r"```json\s*|\s*```", "", text)

    # Ищем первый { или [
    start = text.find("{")
    if start == -1:
        start = text.find("[")
    if start == -1:
        raise ValueError("No JSON object found in response")

    bracket_count = 0
    in_string = False
    escape = False
    end = len(text) - 1

    for i, ch in enumerate(text[start:], start=start):
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"' and not escape:
            in_string = not in_string
            continue
        if not in_string:
            if ch in "{[":
                bracket_count += 1
            elif ch in "}]":
                bracket_count -= 1
                if bracket_count == 0:
                    end = i
                    break

    # Если дошли до конца, но скобки не закрыты — пробуем закрыть сами
    if bracket_count > 0:
        # Добавляем недостающие закрывающие скобки
        if text[start] == "{":
            closing = "}" * bracket_count
        else:
            closing = "]" * bracket_count
        return text[start : end + 1] + closing

    return text[start : end + 1]


def build_prompt(user_query: str) -> str:
    return f"""Ты — помощник. Отвечай ТОЛЬКО на русском языке. Запрещены китайские иероглифы.

Пользователь хочет: "{user_query}"

Сгенерируй JSON по схеме:
{{"category": "категория (3-8 слов)", "skills": [{{"name": "название (2-6 слов)", "initial_level": 1, "target_level": 6, "description": "текст"}}], "connections": [{{"from_skill": "название", "to_skill": "название", "label": "текст (до 80 символов)"}}]}}

ОГРАНИЧЕНИЯ (строго соблюдай):
- Количество навыков (skills): от 3 до 8.
- Количество связей (connections): от 0 до 4. Может быть 0, если связи не очевидны.
- Длина названия навыка (name): от 2 до 6 слов.
- Длина описания (description): до 400 символов.
- Длина связи (label): до 80 символов.

ТРЕБОВАНИЯ К description (ОБЯЗАТЕЛЬНО):
1. Начинай с "Вы научитесь", "Вы освоите" или "Вы сможете".
2. Укажи что изучите.
3. Укажи что сможете сделать на практике.
4. Укажи ресурсы (2-4 разных ресурса). РЕСУРСЫ В КАЖДОМ НАВЫКЕ ДОЛЖНЫ БЫТЬ РАЗНЫМИ. ЗАПРЕЩЕНО ПОВТОРЯТЬ ОДИН И ТОТ ЖЕ РЕСУРС В РАЗНЫХ НАВЫКАХ.
5. Укажи время в часах или днях.
6. initial_level всегда 1.
7. target_level от 5 до 8.

ПРИМЕРЫ С РАЗНЫМИ РЕСУРСАМИ (обязательно соблюдай разнообразие):

Пример 1 (SQL):
"Вы научитесь писать SELECT и JOIN. Сможете анализировать данные из 2 таблиц. Ресурсы: Stepik, SQL-ex.ru. Время: 10 часов"

Пример 2 (Python):
"Вы освоите pandas и numpy. Сможете обрабатывать CSV с миллионом строк. Ресурсы: YouTube канал 'Типичный программист', книга 'Python для анализа данных'. Время: 20 часов"

Пример 3 (Дизайн):
"Вы изучите основы Figma. Сможете создавать макеты сайтов и прототипы. Ресурсы: блог Figma, сообщество дизайнеров в Telegram. Время: 15 часов"

Пример 4 (Unity):
"Вы научитесь создавать игровые объекты в Unity. Сможете собрать простую 2D игру. Ресурсы: официальная документация Unity, форум Unity Answers. Время: 25 часов"

ВАЖНО: Не повторяй ресурсы! Если в одном навыке уже был Stepik, во втором напиши YouTube, в третьем — книгу, в четвёртом — документацию.

Сгенерируй для: {user_query}"""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type(Exception),
)
async def call_ollama(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "format": "json",
                "stream": False,
                "options": {"temperature": 0.0},
            },
        )
        response.raise_for_status()
        raw_text = response.text

        logger.debug(f"Raw HTTP response: {raw_text[:500]}")

        # Извлекаем внешний JSON из ответа Ollama
        outer_json_str = extract_first_json(raw_text)
        outer_data = json.loads(outer_json_str)

        # Получаем поле content, где лежит итоговый JSON
        content = outer_data.get("message", {}).get("content", "")
        if not content:
            raise ValueError("Missing 'message.content' in Ollama response")

        # Извлекаем первый JSON из content (на случай, если модель добавила пояснения)
        try:
            final_json = extract_first_json(content)
            # Проверяем, что это валидный JSON
            json.loads(final_json)
            return final_json
        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"Failed to extract JSON from content: {content[:500]}")
            # Возвращаем fallback JSON, чтобы не падать
            fallback = json.dumps(
                {
                    "category": "Ошибка генерации",
                    "skills": [
                        {
                            "name": "Попробуйте ещё раз",
                            "initial_level": 1,
                            "target_level": 6,
                            "description": "Нейросеть не смогла корректно сгенерировать ответ. Пожалуйста, измените запрос или попробуйте позже.",
                        }
                    ],
                    "connections": [],
                },
                ensure_ascii=False,
            )
            return fallback
