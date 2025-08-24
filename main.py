from preprocess import clean_text, detect_language
from sentiment_model import analyze_sentiment
import matplotlib.pyplot as plt

# Store history of results for visualization
history = {"Positive": 0, "Negative": 0, "Neutral": 0}

def run_analysis(text: str):
    # Step 1: Preprocess text
    cleaned_text = clean_text(text)
    lang = detect_language(cleaned_text)

    # Step 2: Run sentiment model
    sentiment = analyze_sentiment(cleaned_text, lang)

    # Step 3: Save result to history
    history[sentiment] += 1

    # Step 4: Show result
    print("\n🔎 Input Text:", text)
    print("🧹 Cleaned Text:", cleaned_text)
    print("🌍 Detected Language:", lang)
    print("📊 Sentiment:", sentiment)

def show_visualizations():
    sentiments = list(history.keys())
    counts = list(history.values())

    # Pie chart
    plt.figure(figsize=(6,6))
    plt.pie(counts, labels=sentiments, autopct='%1.1f%%', startangle=140)
    plt.title("Sentiment Distribution")
    plt.show()

    # Bar chart
    plt.figure(figsize=(6,4))
    plt.bar(sentiments, counts, color=['green','red','gray'])
    plt.title("Sentiment Count")
    plt.xlabel("Sentiment")
    plt.ylabel("Count")
    plt.show()

if __name__ == "__main__":
    print("🚀 Sentiment Analysis System Ready")
    print("Type 'exit' to quit and show visualization.\n")

    while True:
        user_input = input("👉 Enter text / review / comment: ")
        if user_input.lower() == "exit":
            print("\n📊 Generating Visualizations...")
            show_visualizations()
            print("👋 Exiting Sentiment Analyzer")
            break
        run_analysis(user_input)
