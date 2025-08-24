import re
from langdetect import detect, DetectorFactory

# Fix randomness in langdetect
DetectorFactory.seed = 0

def clean_text(text: str) -> str:
    """
    Cleans raw text by removing URLs, mentions, hashtags, emojis, etc.
    """
    text = text.lower()
    text = re.sub(r"http\S+|www\S+", "", text)   # remove URLs
    text = re.sub(r"@\w+", "", text)             # remove mentions
    text = re.sub(r"#\w+", "", text)             # remove hashtags
    text = re.sub(r"[^a-zA-Z0-9\u0900-\u097F\u0B80-\u0BFF\s]", "", text) # keep English, Hindi, Tamil
    text = re.sub(r"\s+", " ", text).strip()     # remove extra spaces
    return text

def detect_language(text: str) -> str:
    """
    Detects language: English, Hindi, or Tamil
    """
    try:
        lang = detect(text)
        if lang == "en":
            return "English"
        elif lang == "hi":
            return "Hindi"
        elif lang == "ta":
            return "Tamil"
        else:
            return "English"  # default fallback
    except:
        return "English"
