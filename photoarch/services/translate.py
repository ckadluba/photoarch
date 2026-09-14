import logging

import requests
from deep_translator import GoogleTranslator
import deep_translator.google as deep_translator_google

logger = logging.getLogger(__name__)
_requests_get = requests.get


def _get_with_redirect(url, **kwargs):
    kwargs["allow_redirects"] = False
    response = _requests_get(url, **kwargs)

    if response.status_code == 302:
        location = response.headers.get("Location")
        logger.warning(
            "Google Translate returned HTTP 302; retrying with the URL from the Location header."
        )
        if location:
            response.close()
            response = _requests_get(location, **kwargs)

    return response


def translate_english_to_german(text: str) -> str:
    result: str = ""

    translator = GoogleTranslator(source="en", target="de")

    try:
        original_get = deep_translator_google.requests.get
        deep_translator_google.requests.get = _get_with_redirect
        try:
            result = translator.translate(text)
        finally:
            deep_translator_google.requests.get = original_get
    except Exception:
        result = ""

    return result
