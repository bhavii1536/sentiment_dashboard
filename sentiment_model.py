import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
nltk.download('vader_lexicon')
vader = SentimentIntensityAnalyzer()

# Simple lexicons
hindi_lexicon = {"अच्छा":"Positive","खुश":"Positive","पसंद":"Positive","बुरा":"Negative","गुस्सा":"Negative"}
tamil_lexicon = {"நல்ல":"Positive","சந்தோஷம்":"Positive","அருமை":"Positive","கெட்ட":"Negative","கோபம்":"Negative"}

def analyze_sentiment(text, lang="English"):
    text = text.strip().lower()
    if lang=="English":
        scores = vader.polarity_scores(text)
        if scores['compound'] >= 0.05: return "Positive"
        elif scores['compound'] <= -0.05: return "Negative"
        else: return "Neutral"
    elif lang=="Hindi":
        for w in hindi_lexicon:
            if w in text: return hindi_lexicon[w]
        return "Neutral"
    elif lang=="Tamil":
        for w in tamil_lexicon:
            if w in text: return tamil_lexicon[w]
        return "Neutral"
    else:
        return "Neutral"
