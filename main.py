from preprocess import clean_text, detect_language
from sentiment_model import analyze_sentiment
from fetch_data import fetch_twitter_data, fetch_youtube_by_keyword
from collections import Counter

def run_analysis(keyword, max_items=100):
    print(f"Fetching data for: {keyword} ...")
    
    tweets = fetch_twitter_data(keyword, max_items)
    yt_comments = fetch_youtube_by_keyword(keyword, max_videos=5, max_comments_per_video=max_items//5)

    records = []
    # Twitter
    for t in tweets:
        txt = clean_text(t)
        lg = detect_language(txt)
        sent = analyze_sentiment(txt, lg)
        records.append({"text": t, "clean": txt, "lang": lg, "sent": sent, "src": "Twitter"})
    # YouTube
    for yt in yt_comments:
        txt = clean_text(yt["text"])
        lg = detect_language(txt)
        sent = analyze_sentiment(txt, lg)
        records.append({"text": yt["text"], "clean": txt, "lang": lg, "sent": sent, "src": "YouTube"})

    # Summary
    cnt = Counter([r["sent"] for r in records])
    print("\nSentiment Distribution:")
    print(cnt)

    pos_comments = [r["text"] for r in records if r["sent"] == "Positive"]
    neg_comments = [r["text"] for r in records if r["sent"] == "Negative"]

    print("\nTop Positive Comments:")
    for c in pos_comments[:10]:
        print("-", c)
    print("\nTop Negative Comments:")
    for c in neg_comments[:10]:
        print("-", c)

if __name__ == "__main__":
    while True:
        keyword = input("Enter product/topic (or 'exit' to quit): ")
        if keyword.lower() == "exit":
            break
        run_analysis(keyword)
