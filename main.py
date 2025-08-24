from preprocess import clean_text, detect_language
from sentiment_model import analyze_sentiment

def run_analysis(text: str):
    # Step 1: Preprocess text
    cleaned_text = clean_text(text)
    lang = detect_language(cleaned_text)

    # Step 2: Run sentiment model
    sentiment = analyze_sentiment(cleaned_text, lang)

    # Step 3: Show result
    print("\n🔎 Input Text:", text)
    print("🧹 Cleaned Text:", cleaned_text)
    print("🌍 Detected Language:", lang)
    print("📊 Sentiment:", sentiment)

if __name__ == "__main__":
    print("🚀 Sentiment Analysis System Ready")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("👉 Enter text / review / comment: ")
        if user_input.lower() == "exit":
            print("👋 Exiting Sentiment Analyzer")
            break
        run_analysis(user_input)
