import re

def extract_leave_date(text: str) -> str | None:
    """
    Extracts a leave date from natural language email text.

    Examples matched:
    - "May 21, 2025"
    - "June 5"
    - "Jul 4th"

    Returns:
        The matched date string if found, else None.
    """
    pattern = r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|' \
              r'May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|' \
              r'Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}' \
              r'(?:st|nd|rd|th)?(?:,?\s+\d{4})?'
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(0) if match else None
