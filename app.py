# app.py
import json
import streamlit as st
from preprocess import clean_text, detect_language
from sentiment_model import analyze_sentiment
from fetch_data import fetch_twitter_data, fetch_youtube_by_keyword, fetch_youtube_by_channel
from visualize import plot_sentiment_pie, plot_platform_bar
import nltk
from collections import Counter
import re

# ---- NLTK setup for pros/cons extraction ----
nltk.download('punkt')
nltk.download('stopwords')
from nltk.corpus import stopwords
STOPWORDS = set(stopwords.words('english'))

# ---- load translations ----
with open("translations.json", "r", encoding="utf-8") as f:
    I18N = json.load(f)

def t(lang, key, fallback=None):
    return I18N.get(lang, {}).get(key, fallback or key)

def extract_feedback(comments, top_n=5):
    """Extract top short words/phrases from comments"""
    words = []
    for c in comments:
        text = c.lower()
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        tokens = nltk.word_tokenize(text)
        tokens = [w for w in tokens if w not in STOPWORDS and len(w) > 2]
        words.extend(tokens)
    most_common = [w for w, _ in Counter(words).most_common(top_n)]
    return most_common

# ---- Streamlit Page Setup ----
st.set_page_config(page_title="Sentiment Dashboard", layout="wide")
st.sidebar.title("📊 Sentiment Dashboard")

# ---- Language Selection ----
lang_dict = {"English": "en", "Tamil": "ta", "Hindi": "hi"}
lang_name = st.sidebar.selectbox("🌐 Language", ["English", "Tamil", "Hindi"], index=0)
lang = lang_dict[lang_name]

# ---- Menu ----
menu = st.sidebar.radio(
    t(lang, "menu", "Menu"),
    [t(lang,"product_analysis","Product / Feedback Analysis"),
     t(lang,"creator_insights","Content Creator Insights")]
)

st.title(t(lang, "app_title", "Sentiment Analysis Dashboard"))
st.caption(t(lang, "tagline", "Fast, multilingual (Tamil/English/Hindi), emoji-aware"))

# ====== PRODUCT / FEEDBACK ANALYSIS ======
if menu == t(lang,"product_analysis","Product / Feedback Analysis"):
    st.subheader(t(lang, "select_product", "Enter Product Name / Keyword"))
    col1, col2 = st.columns([2,1])
    with col1:
        keyword = st.text_input(t(lang, "product_name", "Product / Topic Name"), placeholder="e.g., iPhone 15")
    with col2:
        max_items = st.number_input(t(lang, "items_per_platform", "Items per platform"), min_value=50, max_value=400, value=200, step=50)

    if st.button(t(lang, "analyze_button", "Analyze"), use_container_width=True) and keyword.strip():
        with st.spinner(t(lang, "fetching_data", "Fetching latest data…")):
            tweets = fetch_twitter_data(keyword, limit=max_items)
            yt_comments = fetch_youtube_by_keyword(keyword, max_videos=5, max_comments_per_video=max_items//5)

        # Shape into unified records and analyze
        records = []
        for txt in tweets:
            cleaned = clean_text(txt)
            lg = detect_language(cleaned)
            sent = analyze_sentiment(cleaned, lg)
            records.append({"text": txt, "clean": cleaned, "lang": lg, "sent": sent, "src": "Twitter", "views": 0})

        for item in yt_comments:
            cleaned = clean_text(item["text"])
            lg = detect_language(cleaned)
            sent = analyze_sentiment(cleaned, lg)
            records.append({"text": item["text"], "clean": cleaned, "lang": lg, "sent": sent, "src": "YouTube", "views": item.get("viewCount",0)})

        # ---- Charts ----
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(plot_sentiment_pie(records), use_container_width=True)

        with c2:
            # Platform comparison based on total views (Twitter: count, YouTube: sum views)
            platform_counts = {"Twitter": sum(1 for r in records if r["src"]=="Twitter"),
                               "YouTube": sum(r.get("views",0) for r in records if r["src"]=="YouTube")}
            st.bar_chart(platform_counts)

        # ---- Pros / Cons extraction ----
        pos_comments = [r["text"] for r in records if r["sent"]=="Positive"]
        neg_comments = [r["text"] for r in records if r["sent"]=="Negative"]

        top_pros = extract_feedback(pos_comments, top_n=5)
        top_cons = extract_feedback(neg_comments, top_n=5)

        st.markdown("### Pros / Positive Feedback")
        for p in top_pros:
            st.write(f"- {p}")

        st.markdown("### Cons / Negative Feedback")
        for c in top_cons:
            st.write(f"- {c}")

# ====== CONTENT CREATOR INSIGHTS (YOUTUBE) ======
if menu == t(lang,"creator_insights","Content Creator Insights"):
    st.subheader(t(lang, "select_channel", "Enter YouTube Channel ID"))
    col1, col2 = st.columns([2,1])
    with col1:
        channel_id = st.text_input(t(lang, "channel_id", "Channel ID"), placeholder="e.g., UC_x5XG1OV2P6uZZ5FSM9Ttw")
    with col2:
        max_videos = st.number_input(t(lang, "videos_to_analyze", "Videos to analyze"), min_value=5, max_value=50, value=20, step=5)
    max_comments = st.slider(t(lang, "comments_per_video", "Comments per video"), 50, 300, 200, 50)

    if st.button(t(lang, "analyze_channel", "Analyze Channel"), use_container_width=True) and channel_id.strip():
        with st.spinner(t(lang, "fetching_channel", "Fetching channel comments…")):
            yt_comments = fetch_youtube_by_channel(channel_id, max_videos=max_videos, max_comments_per_video=max_comments)

        records = []
        for item in yt_comments:
            cleaned = clean_text(item["text"])
            lg = detect_language(cleaned)
            sent = analyze_sentiment(cleaned, lg)
            rec = {"text": item["text"], "clean": cleaned, "lang": lg, "sent": sent, "src": "YouTube",
                   "videoTitle": item.get("videoTitle",""), "views": item.get("viewCount", 0)}
            records.append(rec)

        # Sentiment Pie Chart
        st.plotly_chart(plot_sentiment_pie(records), use_container_width=True)

        # Platform comparison (just YouTube here)
        platform_views = {"YouTube": sum(r.get("views",0) for r in records)}
        st.bar_chart(platform_views)

        # Quick KPIs
        pos = sum(1 for r in records if r["sent"]=="Positive")
        neg = sum(1 for r in records if r["sent"]=="Negative")
        neu = sum(1 for r in records if r["sent"]=="Neutral")
        total = max(1, len(records))
        colA, colB, colC, colD = st.columns(4)
        colA.metric("Total Comments", f"{total}")
        colB.metric("Positive %", f"{(pos/total)*100:0.1f}%")
        colC.metric("Neutral %", f"{(neu/total)*100:0.1f}%")
        colD.metric("Negative %", f"{(neg/total)*100:0.1f}%")

st.caption("Tip: Set your YT API key in Streamlit secrets as YOUTUBE_API_KEY. Twitter uses snscrape fallback.")
