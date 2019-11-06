import re

def normalize_description(text):
    return re.sub(r'\n+', '', text)
    