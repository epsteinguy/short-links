import string
import random

CHARACTERS = string.ascii_letters + string.digits

def generate_short_code(lenght: int = 6) -> str:
    """Generate a random short code."""
    return ''.join(random.choices(CHARACTERS, k=lenght))

def generate_unique_short_code(db, lenght: int = 6, max_attempts: int = 10) -> str:
    """Genrate a short code that doesnt exist yet"""
    from app.models import URL

    for _ in range(max_attempts):
        code = generate_short_code(lenght)
        existing = db.query(URL).filter(URL.short_code == code).first()
        if not existing:
            return code
        return generate_unique_short_code(db, lenght + 1, max_attempts)
