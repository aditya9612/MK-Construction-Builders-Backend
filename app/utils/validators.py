import re

INDIAN_MOBILE = re.compile(r"^[6-9]\d{9}$")


def validate_indian_mobile(value: str) -> str:
    cleaned = re.sub(r"[\s\-]", "", value)
    if cleaned.startswith("+91"):
        cleaned = cleaned[3:]
    if cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]
    if not INDIAN_MOBILE.match(cleaned):
        raise ValueError("Mobile must be a valid 10-digit Indian number")
    return cleaned
