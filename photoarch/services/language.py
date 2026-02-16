from deep_translator import GoogleTranslator


def translate_english_to_german(text: str) -> str:
    result: str = ""

    translator = GoogleTranslator(source="en", target="de")

    try:
        result = translator.translate(text)
    except Exception:
        result = ""

    return result
