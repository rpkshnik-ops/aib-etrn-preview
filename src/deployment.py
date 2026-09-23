import re
from urllib.parse import urlsplit


def settings(values=None):
    result = {
        "mode": "preview", "site_url": "", "privacy_url": "",
        "consent_url": "", "offer_url": "", "delivery_confirmed": False,
        "metrica_id": "",
    }
    if values:
        unknown = set(values) - set(result)
        if unknown:
            raise ValueError("Unknown settings: " + ", ".join(sorted(unknown)))
        result.update(values)
    if result["mode"] not in {"preview", "staging", "production"}:
        raise ValueError("mode must be preview, staging or production")
    for name in ("site_url", "privacy_url", "consent_url", "offer_url"):
        value = result[name]
        if not isinstance(value, str):
            raise ValueError(f"{name} must be a URL string")
        if not value:
            continue
        url = urlsplit(value)
        if (url.scheme != "https" or not url.hostname or url.username or url.password
                or url.query or url.fragment or any(c.isspace() for c in value)):
            raise ValueError(f"{name}: use an absolute HTTPS URL without query/fragment")
        if name == "site_url":
            if url.path not in ("", "/"):
                raise ValueError("Server deployment requires a domain root, not a subdirectory")
            result[name] = value.rstrip("/") + "/"
    if type(result["delivery_confirmed"]) is not bool:
        raise ValueError("delivery_confirmed must be true or false")
    counter = str(result["metrica_id"])
    if counter and not re.fullmatch(r"[0-9]{5,12}", counter):
        raise ValueError("metrica_id must contain 5–12 digits")
    result["metrica_id"] = counter
    if result["mode"] == "production":
        for name in ("site_url", "privacy_url", "consent_url", "offer_url"):
            if not result[name] or "YOUR-DOMAIN" in result[name].upper():
                raise ValueError(f"Production requires an actual {name}")
        if not result["delivery_confirmed"]:
            raise ValueError("Confirm a received test lead before enabling production")
    return result
