import json
import logging
import time

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
_requests_get = requests.get
_GOOGLE_TRANSLATE_URL = "https://translate.googleapis.com/translate_a/single"
_FALLBACK_TRANSLATE_URL = "https://api.mymemory.translated.net/get"


def _get_with_retry_after(url, **kwargs):
    response = _requests_get(url, **kwargs)

    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After")
        try:
            wait_seconds = float(retry_after)
        except TypeError, ValueError:
            logger.warning(
                "Google Translate returned HTTP 429 without a valid Retry-After header."
            )
        else:
            logger.warning(
                "Google Translate returned HTTP 429; retrying after %.1f seconds.",
                wait_seconds,
            )
            response.close()
            time.sleep(wait_seconds)
            response = _requests_get(url, **kwargs)

    return response


def _get_with_redirect(url, **kwargs):
    kwargs["allow_redirects"] = False
    response = _get_with_retry_after(url, **kwargs)

    if response.status_code == 302:
        location = response.headers.get("Location")
        logger.warning(
            "Google Translate returned HTTP 302; retrying with the URL from the Location header."
        )
        if location:
            response.close()
            response = _get_with_retry_after(location, **kwargs)

    return response


def _parse_translation(response: requests.Response) -> str:
    try:
        data = json.loads(response.text)
    except TypeError, json.JSONDecodeError:
        soup = BeautifulSoup(response.text, "html.parser")
        element = soup.find("div", class_="t0") or soup.find(
            "div", class_="result-container"
        )
        return element.get_text(strip=True) if element else ""

    return "".join(segment[0] for segment in data[0] if segment and segment[0])


def _translate_with_fallback(text: str) -> str:
    response = requests.get(
        _FALLBACK_TRANSLATE_URL,
        params={"q": text, "langpair": "en|de"},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("responseData", {}).get("translatedText", "")


def translate_english_to_german(text: str) -> str:
    result: str = ""

    try:
        response = _get_with_redirect(
            _GOOGLE_TRANSLATE_URL,
            params={"client": "gtx", "sl": "en", "tl": "de", "dt": "t", "q": text},
        )
        if response.status_code == 200:
            result = _parse_translation(response)
        else:
            logger.warning(
                "Google Translate returned HTTP %s after retries; using fallback translation service.",
                response.status_code,
            )
            result = _translate_with_fallback(text)
    except Exception:  # noqa: BLE001 - translation failures are non-fatal
        result = ""

    return result
