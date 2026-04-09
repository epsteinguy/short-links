import re
import string
import random

CHARACTERS = string.ascii_letters + string.digits

RESERVED_WORDS = {
    "admin", "api", "health", "docs", "shorten",
    "login", "register", "static", "assets", "favicon"
}


def generate_short_code(length: int = 6) -> str:
    return "".join(random.choices(CHARACTERS, k=length))


def generate_unique_short_code(db, length: int = 6, max_attempts: int = 10) -> str:
    from app.models import URL

    for _ in range(max_attempts):
        code = generate_short_code(length)
        existing = db.query(URL).filter(URL.short_code == code).first()
        if not existing:
            return code

    return generate_unique_short_code(db, length + 1, max_attempts)


def validate_custom_code(code: str) -> tuple[bool, str]:
    if len(code) < 3:
        return False, "Custom code must be at least 3 characters"
    if len(code) > 20:
        return False, "Custom code must be 20 characters or less"
    if not re.match(r"^[a-zA-Z0-9-]+$", code):
        return False, "Custom code can only contain letters, numbers, and hyphens"
    if code.startswith("-") or code.endswith("-"):
        return False, "Custom code cannot start or end with a hyphen"
    if code.lower() in RESERVED_WORDS:
        return False, f"'{code}' is a reserved word and cannot be used"
    return True, ""


def is_code_available(db, code: str) -> bool:
    from app.models import URL
    existing = db.query(URL).filter(URL.short_code == code).first()
    return existing is None
