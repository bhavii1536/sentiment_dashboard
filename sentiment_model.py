import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import re

# Download VADER once
nltk.download('vader_lexicon')

# Initialize VADER for English
vader = SentimentIntensityAnalyzer()

# Simple Hindi & Tamil sentiment dictionaries (expand as needed)
hindi_lexicon = {
    "अच्छा": "Positive", "खुश": "Positive", "पसंद": "Positive",
    "बुरा": "Negative", "गुस्सा": "Negative", "नफरत": "Negative"
}

tamil_lexicon = {
    "நல்ல": "Positive", "சந்தோஷம்": "Positive", "அருமை": "Positive",
    "கெட்ட": "Negative", "கோபம்": "Negative", "வெறுப்பு": "Negative"
}

def analyze_sentiment(text, lang="English"):
    """
    Analyze sentiment based on language.
    Returns: "Positive", "Negative", "Neutral"
    """

    # Clean text
    text = text.strip().lower()

    # English → VADER
    if lang == "English":
        scores = vader.polarity_scores(text)
        if scores['compound'] >= 0.05:
            return "Positive"
        elif scores['compound'] <= -0.05:
            return "Negative"
        else:
            return "Neutral"

    # Hindi → Simple lexicon
    elif lang == "Hindi":
        for word in hindi_lexicon:
            if word in text:
                return hindi_lexicon[word]
        return "Neutral"

    # Tamil → Simple lexicon
    elif lang == "Tamil":
        for word in tamil_lexicon:
            if word in text:
                return tamil_lexicon[word]
        return "Neutral"

    else:
        return "Neutral"
