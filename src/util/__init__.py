def matches_prefixes(text: str, prefixes: list):
    for prefix in prefixes:
        if text.startswith(prefix):
            return True
    return False
