import re
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0

def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"http\S+|www\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"#\w+", "", text)
    text = re.sub(r"[^a-zA-Z0-9\u0900-\u097F\u0B80-\u0BFF\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def detect_language(text: str) -> str:
    try:
        lang = detect(text)
        if lang=="en": return "English"
        elif lang=="hi": return "Hindi"
        elif lang=="ta": return "Tamil"
        else: return "English"
    except:
        return "English"
